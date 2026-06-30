#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/exascale/tests_vm_move.py /main/41 2026/02/10 17:09:05 scoral Exp $
#
# tests_vm_move.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_vm_move.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    06/11/26 - Update vm move unit tests for vm_maker cleanup
#    dekuckre    04/27/26 - fix vm_move unit tests
#    dekuckre    04/27/26 - remove unnecessary DB setup for vm_move unit tests
#    siyarlag    01/23/26 - Fix nft fallback test expectation
#    nelango     01/23/26 - Add unit test for busy mount message
#    dekuckre    12/19/25 - Codex UT enhancement
#    prsshukl    07/12/25 - Bug 38176800 -> Updating test case for validate
#                           volumes
#    prsshukl    06/27/25 - Enh 37747083 - Added check for
#                           mPerformValidateVolumesCheck
#    scoral      05/06/25 - Bug 37665235 - Improved
#                           test_005_vm_move_prechecks_oeda to include mock
#                           commands for source host checks.
#    scoral      03/28/25 - Bug 37756495 - Added unit tests for
#                           mPostVMMoveSteps
#    asrigiri    10/31/24 - Bug 36981061 - EXACC:LOCAL FS RESIZE FETCHES ALL FS
#                           DETAILS INCLUDING NFS MOUNTS
#    prsshukl    05/11/24 - Bug 36608539 - Fix test_001_vm_move_exacloud
#    gparada     10/11/23 - Bug 35891714 Fix test_004_vm_move_prechecks mock
#    jfsaldan    09/04/23 - Bug 35759673 - EXACS:23.4.1:XEN:FILE SYSTEM
#                           ENCRYPTION:SKIP U02 RESIZE ON XEN IF ENCRPYTED
#    gparada     08/01/23 - Added scenario to skip VmMoveSanityChecks on EDV
#    jesandov    12/06/22 - Creation
#

import json
import os
import re
import unittest
import shutil
from exabox.core.Context import get_gcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch, call, ANY

from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluexascale import VM_MAKER, ebCluExaScale, EDVState, mRemoveVMmount
from exabox.utils.node import CmdRet
from exabox.ovm.clucommandhandler import CommandHandler
def myRun(FromXml, ToXml):
    shutil.copyfile(FromXml, ToXml)

class ebTestVmMove(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=False, aUseOeda=True)
        self.mGetClubox(self).mSetExaScale(True)
        self.mGetClubox(self).mSetDebug(True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_validate_import_export', "False")

    def _build_oeda_sanity_options(self, vm_name="testvm"):
        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": vm_name,
            "target_dom0_name": "dom0-target",
            "source_dom0_name": "dom0-source"
        }
        return _options

    def _build_exacloud_sanity_options(self, vm_name="testvm"):
        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": vm_name,
            "target_dom0_name": "dom0-target",
            "source_dom0_name": "dom0-source"
        }
        return _options

    def _build_backup_network_ebox(self, network_types, base=True, exacompute=False):
        _ebox = MagicMock()
        _ebox.isBaseDB.return_value = base
        _ebox.isExacomputeVM.return_value = exacompute
        _ebox.mGetUUID.return_value = "uuid"
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mGetPatchConfig.return_value = "/patch/config.xml"
        _ebox.mGetOedaPath.return_value = "/oeda"
        _ebox.mExecuteLocal = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu")]

        _machines = MagicMock()
        _machine_config = MagicMock()
        _machine_config.mGetMacNetworks.return_value = list(network_types.keys())
        _machines.mGetMacIdFromMacHostName.return_value = "machine1"
        _machines.mGetMachineConfig.return_value = _machine_config
        _ebox.mGetMachines.return_value = _machines

        _network_configs = {}
        for _net_id, _net_type in network_types.items():
            _cfg = MagicMock()
            _cfg.mGetNetType.return_value = _net_type
            _cfg.mGetInterfaceName.return_value = "iface"
            _network_configs[_net_id] = _cfg

        _networks = MagicMock()

        def _get_network_config(_net_id):
            return _network_configs[_net_id]

        _networks.mGetNetworkConfig.side_effect = _get_network_config
        _ebox.mGetNetworks.return_value = _networks

        return _ebox


    def _build_dom0_network_options(self, roce_information=None):
        _options = self.mGetPayload()
        if roce_information is None:
            roce_information = {}
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": "testvm",
            "roce_information": roce_information,
        }
        return _options

    def _build_interface_removal_ebox(self, networks, base=True, exacompute=False, db_on_volumes=False):
        _ebox = MagicMock()
        _ebox.isDBonVolumes.return_value = db_on_volumes
        _ebox.isBaseDB.return_value = base
        _ebox.isExacomputeVM.return_value = exacompute
        _ebox.mGetUUID.return_value = "uuid"
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mGetPatchConfig.return_value = "/patch/config.xml"
        _ebox.mGetOedaPath.return_value = "/oeda"
        _ebox.mExecuteLocal = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu")]

        _machines = MagicMock()
        _machine_config = MagicMock()
        _machine_config.mGetMacNetworks.return_value = [net[0] for net in networks]
        _machines.mGetMacIdFromMacHostName.return_value = "machine1"
        _machines.mGetMachineConfig.return_value = _machine_config
        _ebox.mGetMachines.return_value = _machines

        _network_configs = {}
        for _net_id, _net_type, _iface in networks:
            _cfg = MagicMock()
            _cfg.mGetNetType.return_value = _net_type
            _cfg.mGetInterfaceName.return_value = _iface
            _network_configs[_net_id] = _cfg

        _networks = MagicMock()

        def _get_network_config(_net_id):
            return _network_configs[_net_id]

        _networks.mGetNetworkConfig.side_effect = _get_network_config
        _ebox.mGetNetworks.return_value = _networks

        return _ebox


    def _build_volume_ebox(self, *, base=False, db_on_volumes=False, exacompute=False, jsonconf=None, config_overrides=None):
        _ebox = MagicMock()
        _ebox.isBaseDB.return_value = base
        _ebox.isDBonVolumes.return_value = db_on_volumes
        _ebox.isExacomputeVM.return_value = exacompute
        _ebox.mGetUUID.return_value = "uuid"
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mGetPatchConfig.return_value = "/patch/config.xml"
        _ebox.mGetOedaPath.return_value = "/oeda"
        _ebox.mExecuteLocal = MagicMock(return_value=(0, "", "", ""))
        _ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu")]

        _clusters = MagicMock()
        _cluster = MagicMock()
        _cluster.mGetCluName.return_value = "cluster"
        _clusters.mGetCluster.return_value = _cluster
        _ebox.mGetClusters.return_value = _clusters

        _options = SimpleNamespace(jsonconf=jsonconf or {})
        _ebox.mGetOptions.return_value = _options

        _config = {
            "exascale_edv_enable": "True",
            "override_volume_file": "",
            "exadbxs_19c_invoke_oedacli": "False",
        }
        if config_overrides:
            _config.update(config_overrides)

        def _check(option, default=None):
            if default is None:
                return _config.get(option)
            return _config.get(option, default)

        _ebox.mCheckConfigOption.side_effect = _check
        return _ebox, _options

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_backup_network_guard_skip(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveDomUBackupNetwork guard branch
        _ebox = self._build_backup_network_ebox({"net1": "backup"}, base=False, exacompute=False)
        _exascale = ebCluExaScale(_ebox)

        _exascale.mRemoveDomUBackupNetwork()

        _ebox.mExecuteLocal.assert_not_called()
        mock_tree.assert_not_called()
        mock_oedacli.assert_not_called()

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_backup_network_executes_oedacli(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveDomUBackupNetwork
        _ebox = self._build_backup_network_ebox({"net1": "backup", "net2": "private"})
        _exascale = ebCluExaScale(_ebox)

        _tree_initial = MagicMock()
        _tree_update = MagicMock()
        mock_tree.side_effect = [_tree_initial, _tree_update]

        _oedacli_instance = MagicMock()
        mock_oedacli.return_value = _oedacli_instance

        _exascale.mRemoveDomUBackupNetwork()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/before_backup_network_removal.xml"
        update_xml = f"{local_prefix}/after_backup_network_removal.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        self.assertEqual(mock_tree.call_args_list, [call("/patch/config.xml"), call(update_xml)])
        _tree_initial.mExportXml.assert_called_once_with(initial_xml)
        _tree_update.mExportXml.assert_called_once_with("/patch/config.xml")

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        _oedacli_instance.mAppendCommand.assert_called_once_with("DELETE NETWORK", None, {"ID": "net1"})
        _oedacli_instance.mRun.assert_called_once_with(initial_xml, update_xml)

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_backup_network_no_matching_entries(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveDomUBackupNetwork skip branch
        _ebox = self._build_backup_network_ebox({"net1": "private"})
        _exascale = ebCluExaScale(_ebox)

        _tree_initial = MagicMock()
        mock_tree.side_effect = [_tree_initial]

        _oedacli_instance = MagicMock()
        mock_oedacli.return_value = _oedacli_instance

        _exascale.mRemoveDomUBackupNetwork()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/before_backup_network_removal.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        mock_tree.assert_called_once_with("/patch/config.xml")
        _tree_initial.mExportXml.assert_called_once_with(initial_xml)

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        _oedacli_instance.mAppendCommand.assert_not_called()
        _oedacli_instance.mRun.assert_not_called()

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_backup_network_exacompute(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveDomUBackupNetwork ExaCompute branch
        _ebox = self._build_backup_network_ebox({"net1": "backup", "net2": "backup"}, base=False, exacompute=True)
        _exascale = ebCluExaScale(_ebox)

        _tree_initial = MagicMock()
        _tree_update = MagicMock()
        mock_tree.side_effect = [_tree_initial, _tree_update]

        _oedacli_instance = MagicMock()
        mock_oedacli.return_value = _oedacli_instance

        _exascale.mRemoveDomUBackupNetwork()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/before_backup_network_removal.xml"
        update_xml = f"{local_prefix}/after_backup_network_removal.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        self.assertEqual(mock_tree.call_args_list, [call("/patch/config.xml"), call(update_xml)])
        _tree_initial.mExportXml.assert_called_once_with(initial_xml)
        _tree_update.mExportXml.assert_called_once_with("/patch/config.xml")

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        self.assertEqual(
            _oedacli_instance.mAppendCommand.call_args_list,
            [
                call("DELETE NETWORK", None, {"ID": "net1"}),
                call("DELETE NETWORK", None, {"ID": "net2"})
            ]
        )
        _oedacli_instance.mRun.assert_called_once_with(initial_xml, update_xml)

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_interface_in_xml_guard_skip(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveInterfaceInXml guard branch
        _ebox = self._build_interface_removal_ebox([], base=False, exacompute=False, db_on_volumes=False)
        _exascale = ebCluExaScale(_ebox)

        _exascale.mRemoveInterfaceInXml()

        _ebox.mExecuteLocal.assert_not_called()
        mock_tree.assert_not_called()
        mock_oedacli.assert_not_called()

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_interface_in_xml_executes_oedacli(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveInterfaceInXml
        networks = [
            ("net_stre", "private", "stre0"),
            ("net_clre", "private", "clre0"),
        ]
        _ebox = self._build_interface_removal_ebox(networks, base=True)
        _exascale = ebCluExaScale(_ebox)

        _tree_initial = MagicMock()
        _tree_update = MagicMock()
        mock_tree.side_effect = [_tree_initial, _tree_update]

        _oedacli_instance = MagicMock()
        mock_oedacli.return_value = _oedacli_instance

        _exascale.mRemoveInterfaceInXml()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/before_interface_removal.xml"
        update_xml = f"{local_prefix}/after_interface_removal.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        self.assertEqual(mock_tree.call_args_list, [call("/patch/config.xml"), call(update_xml)])
        _tree_initial.mExportXml.assert_called_once_with(initial_xml)
        _tree_update.mExportXml.assert_called_once_with("/patch/config.xml")

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        self.assertEqual(
            _oedacli_instance.mAppendCommand.call_args_list,
            [
                call("DELETE NETWORK", None, {"ID": "net_stre"}),
                call("DELETE NETWORK", None, {"ID": "net_clre"}),
            ]
        )
        _oedacli_instance.mRun.assert_called_once_with(initial_xml, update_xml)

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_remove_interface_in_xml_skip_branch(self, mock_oedacli, mock_tree):
        # Auto-generated test for mRemoveInterfaceInXml skip branch
        networks = [
            ("net_public", "public", "pub0"),
            ("net_private", "private", "eth0"),
        ]
        _ebox = self._build_interface_removal_ebox(networks, base=True)
        _exascale = ebCluExaScale(_ebox)

        _tree_initial = MagicMock()
        mock_tree.return_value = _tree_initial

        _oedacli_instance = MagicMock()
        mock_oedacli.return_value = _oedacli_instance

        _exascale.mRemoveInterfaceInXml()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/before_interface_removal.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        mock_tree.assert_called_once_with("/patch/config.xml")
        _tree_initial.mExportXml.assert_called_once_with(initial_xml)

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        _oedacli_instance.mAppendCommand.assert_not_called()
        _oedacli_instance.mRun.assert_not_called()

    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPerformValidateVolumesCheck")
    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPostVMMoveSteps")
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')
    @patch('socket.gethostbyname', return_value="localhost")
    def test_001_vm_move_exacloud(self, mock_mPerformValidateVolCheck, mock_postvmsteps, mock_myRun, mock_mDom0UpdateCurrentOpLog, mock_socket):

        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand("cp.*", ebTestClucontrol.mRealExecute),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("mkdir.*", aPersist=True),
                    exaMockCommand("ls.*zip.*", aStdout="sample_image.zip"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("cat.*xml.*", aStdout="<domU></domU>"),
                    exaMockCommand("ls.*img.*", aStdout="sample_image.img"),
                    exaMockCommand("bzip2 sample_image.img.*"),
                    exaMockCommand("scp.*bz2.*"),
                    exaMockCommand("vm_maker.*--remove.*", aPersist=True),
                ],
                [
                    exaMockCommand("test.*", aPersist=True),
                ],
                [
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("virsh list.*", aStdout="scaqab10adm01vm08.us.oracle.com"),
                    exaMockCommand("rm.*", aPersist=True),
                    exaMockCommand("sed.*", aPersist=True),
                    exaMockCommand("scp.*", aPersist=True),
                    exaMockCommand("vm_maker.*", aPersist=True),
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("vm_maker.*--start.*"),
                    exaMockCommand("virsh list.*", aStdout="scaqab10adm01vm08.us.oracle.com"),
                    exaMockCommand("virsh.*destroy.*", aPersist=True),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("ls.*bz2.*", aStdout="sample_image.bz2"),
                    exaMockCommand("bunzip2 sample_image.bz2"),
                    exaMockCommand("mv.*img.*"),
                    exaMockCommand("virsh domblklist.*", aStdout="sda u02_extra.img"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("vm_maker.*", aPersist=True),
                ],
                [
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("vm_maker.*--start.*"),
                    exaMockCommand("virsh list.*", aStdout="scaqab10adm01vm08.us.oracle.com"),
                    exaMockCommand("virsh.*destroy.*"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("ls.*bz2.*", aStdout="sample_image.bz2"),
                    exaMockCommand("bunzip2 sample_image.bz2"),
                    exaMockCommand("mv.*img.*"),
                    exaMockCommand("virsh domblklist.*", aStdout="sda u02_extra.img"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("vm_maker.*", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        self.mGetContext().mSetConfigOption("exascale", {"vm_move_api": "exacloud"})
        self.mGetClubox().mSetPatchConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml"))

        # Create XML for test
        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        # Create Exakms key
        _exakms = self.mGetContext().mGetExaKms()
        _privateKey = _exakms.mGetEntryClass().mGeneratePrivateKey()

        _entry = _exakms.mBuildExaKmsEntry("scaqab10adm01vm08.us.oracle.com", "root", _privateKey)
        with patch('exabox.exakms.ExaKmsHistoryDB.ExaKmsHistoryDB.mPutExaKmsHistory'):
            _exakms.mInsertExaKmsEntry(_entry)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "move",
            "vm_name": "scaqab10adm01vm08.us.oracle.com",
            "target_dom0_name": "scaqab10adm07.us.oracle.com",
            "source_dom0_name": "scaqab10adm01.us.oracle.com",
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
        }
        
        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch('exabox.tools.ebOedacli.ebOedacli.mEnsureOedaJavaHome'), \
             patch.object(_exascale, 'mCreateLockObj', return_value=MagicMock()):
            _exascale.mPerformVmMove(_options)


    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.shutdown_domu')
    def test_mremovevmmount_busy_pid_annotation(
        self,
        mock_shutdown,
        mock_get_gctx,
        mock_connect,
        mock_node_exec_cmd_check,
        mock_node_exec_cmd):
        _node = MagicMock(name="dom0_node")

        _ctx = MagicMock()
        _ctx.__enter__.return_value = _node
        _ctx.__exit__.return_value = False
        mock_connect.return_value = _ctx

        mock_node_exec_cmd_check.return_value = CmdRet(0, '', '')

        _vm_name = 'racdbora1.oracle.com'
        _fuser_output = (
            "                     USER        PID ACCESS COMMAND\n"
            f"/EXAVMIMAGES/GuestImages/{_vm_name}:\n"
            "                     root      mount \n"
            "                     root      ..c.. (root)bash\n"
        )

        def _node_exec_cmd_side_effect(node, command, *args, **kwargs):
            if command.startswith(f'/bin/grep {_vm_name} /etc/fstab'):
                return CmdRet(0, f'/dev/exc/gcv_{_vm_name}', '')
            if command.startswith(f'/bin/ls -ld /dev/exc/gcv_{_vm_name}'):
                return CmdRet(0, 'crw------- 1 root root 7 42', '')
            if command.startswith(f'/sbin/fuser -muv /EXAVMIMAGES/GuestImages/{_vm_name}'):
                return CmdRet(0, _fuser_output, '')
            if command.startswith('/bin/dmesg | /bin/grep dev7'):
                return CmdRet(0, '', '')
            if command.startswith(f'/usr/bin/umount /EXAVMIMAGES/GuestImages/{_vm_name}'):
                raise ExacloudRuntimeError(
                    16,
                    0xA,
                    f'EXACLOUD : Remote command execution failed: host=dom0-host; '
                    f'cmd="/usr/bin/umount /EXAVMIMAGES/GuestImages/{_vm_name}"; rc=32; '
                    f'stderr="umount: /EXAVMIMAGES/GuestImages/{_vm_name}: target is busy."'
                )
            return CmdRet(0, '', '')

        mock_node_exec_cmd.side_effect = _node_exec_cmd_side_effect

        with patch('exabox.ovm.cluexascale.ebLogError') as mock_log_error:
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                mRemoveVMmount(MagicMock(), 'dom0-host', _vm_name)

        mock_shutdown.assert_called_once_with(_node, _vm_name, force_on_timeout=True)
        mock_log_error.assert_called_once()
        _logged_msg = mock_log_error.call_args[0][0]
        self.assertIn('root ..c.. (root)bash', _logged_msg)
        self.assertIn(
            f'Unmount of /EXAVMIMAGES/GuestImages/{_vm_name} for VM {_vm_name} in source host dom0-host failed because PID(s) "root mount; root ..c.. (root)bash" are still accessing it.',
            str(ctx.exception)
        )
        ebLogError(_logged_msg)


    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPerformValidateVolumesCheck")
    @patch("exabox.ovm.cluexascale.ebCluExaScale.mSetupNftRules")
    @patch('exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mSetNfTablesExaBM')
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mProbePath", return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('exabox.ovm.cluexascale.version_compare', return_value=-1)
    @patch('socket.gethostbyname', return_value="localhost")
    def test_002_vm_move_oeda(self, mock_mPerformValidateVolCheck, mock_mSetupNftRules, mock_mSetNfTablesExaBM, mock_mRun, mock_mProbePath, mock_mDom0UpdateCurrentOpLog, mock_version_compare, mock_socket):

        _tgtVMBridges = (
            " Interface   Type      Source            Model     MAC\n"
            "----------------------------------------------------------------------\n"
            " -           bridge    vmbondeth0.1239   virtio    00:00:17:01:bc:70\n"
            " -           bridge    vmbondeth0.1240   virtio    00:00:17:01:1a:7c\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:81:5f:4f\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:46:5b:ee\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:90:73:b4\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:53:a7:50\n"
            " -           bridge    vmeth205          virtio    52:54:00:6e:97:ee\n"
        )
        _tgtHostBridges = (
            "bridge name     bridge id               STP enabled     interfaces\n"
            "vmbondeth0\t              8000.b8cef67104a0       no              bondeth0\n"
            "vmeth0\t          8000.001b21e7b71d       no              eth0\n"
            "vmeth0.102\t              8000.001b21e7b71d       no              eth0.102\n"
            "vmeth205\t                8000.2ea3253eabe0       no              eth205\n"
        )
        _vmDisks = (
            " sda      /dev/exc/system_Vmrievh_1_e1f4\n"
            " sdb      /dev/exc/u01_Vmrievh_1_f049\n"
        )
        _interfaces_output = """    <Interfaces>
        <Bridge>dummy</Bridge>
        <Gateway>10.1.0.1</Gateway>
        <Hostname>sea201605exddu0803.localdomain</Hostname>
        <IP_address>10.1.2.31</IP_address>
        <Name>eth0</Name>
        <IP_enabled>yes</IP_enabled>
        <IP_ssh_listen>enabled</IP_ssh_listen>
        <Net_type>Other</Net_type>
        <Netmask>255.255.0.0</Netmask>
        <State>1</State>
        <Status>UP</Status>
        <Vlan_id>101</Vlan_id>
        <nategressipaddresses>10.0.1.0/28</nategressipaddresses>
        <nategressipaddresses>10.0.1.32/28</nategressipaddresses>
        <nategressipaddresses>10.0.1.112/28</nategressipaddresses>
        </Interfaces>"""

        _out = """  sda      /dev/exc/system_Vmnhtzu_3_0d9d
         sdb      /dev/exc/u01_Vmnhtzu_3_0bbf
         sdc      /dev/exc/u02_Vmnhtzu_3_46d9
         """

        _vmXMLPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/vm.xml")
        with open(_vmXMLPath, "r") as _f:
            _vmXML = _f.read()
        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*chmod.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*stage.*", ebTestClucontrol.mRealExecute),
                    MockCommand("cp.*", ebTestClucontrol.mRealExecute),
                    MockCommand("grep*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand("sed*", ebTestClucontrol.mRealExecute, aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*cat.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*cat.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand("nft list chain ip nat PREROUTING .*")
                ],
                [
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*cat.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand(".*mkdir.*"),
                    exaMockCommand(".*mount.*"),
                    exaMockCommand(".*echo.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*ls.*"),
                    exaMockCommand(".*virsh.*", aStdout=_tgtVMBridges),
                    exaMockCommand(".*brctl.*", aStdout=_tgtHostBridges),
                    exaMockCommand(".*ls.*", aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0.102:205"),
                    exaMockCommand(".*cat.*", aStdout="IPADDR=10.0.1.1"),
                    exaMockCommand(".*cat.*", aStdout="IPADDR=169.254.200.1"),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/scaqab10client01vm08.us.oracle.com.xml", aStdout=_vmXML),
                    exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/route-vmeth205"),
                    exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/rule-vmeth205"),
                    exaMockCommand("/bin/virsh domblklist scaqab10client01vm08.us.oracle.com", aStdout=_vmDisks),
                    exaMockCommand("/bin/ls /dev/exc/u02_Vmrievh", aStdout="/dev/exc/u02_Vmrievh_1_31b1"),
                    exaMockCommand("/bin/test -e /dev/exc/u02_Vmrievh_1_31b1"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domblklist scaqab10client01vm08.us.oracle.com | tail -n +3", aStdout=_vmDisks),
                    exaMockCommand("/bin/virsh list", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --attach --disk-image /dev/exc/u02_Vmrievh_1_31b1 --domain scaqab10client01vm08.us.oracle.com "),
                    exaMockCommand("/bin/virsh dumpxml scaqab10client01vm08.us.oracle.com | /bin/grep serial.sock | /bin/cut -d\"/\" -f4", aStdout="341e"),
                    exaMockCommand("/bin/ln -s /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/console/write-qemu /EXAVMIMAGES/console/341e/write-qemu"),
                    exaMockCommand(".*brctl.*", aStdout=_tgtHostBridges),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave eth2 --vlan UNDEFINED --bond-mode active-backup"),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave eth2 --vlan UNDEFINED --bond-mode active-backup"),
                    exaMockCommand("/sbin/ifup bondeth0.UNDEFINED"),
                    exaMockCommand("/sbin/ifup bondeth0.UNDEFINED"),
                    exaMockCommand("/sbin/ifup vmbondeth0.UNDEFINED"),
                    exaMockCommand("/sbin/ifup vmbondeth0.UNDEFINED"),
                    exaMockCommand("/bin/cp -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/scaqab10client01vm08.us.oracle.com.xml /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml"),
                    exaMockCommand("nft list chain ip nat PREROUTING .*")
                ],
                [
                    exaMockCommand(".*mkdir.*"),
                    exaMockCommand(".*mount.*"),
                    exaMockCommand(".*cat.*", aRc=1),
                    exaMockCommand(".*echo.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand("vm_maker.*", aPersist=True),
                    exaMockCommand("/usr/sbin/nft add table ip filter"),
                    exaMockCommand("/usr/sbin/nft add table bridge filter"),
                    exaMockCommand("/bin/ls /dev/exc/gcv_Vm53942_1_b60b"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domiflist .*", aStdout=_tgtVMBridges),
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-vmeth0:205", aStdout="IPADDR=10.0.131.54"),
                    exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-vmeth205", aStdout="IPADDR=10.0.131.54"),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/GuestImages/.*xml", aStdout=_interfaces_output),
                    exaMockCommand("/bin/virsh domblklist .*", aStdout=_out),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-vmeth0.*", aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0:205"),
                    exaMockCommand("/bin/ls /dev/exc/u02_Vmnhtzu_", aStdout="/dev/exc/u02_Vmnhtzu_3_46d9"),
                    exaMockCommand("/bin/test -e /dev/exc/.*"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domblklist scaqab10client01vm08.us.oracle.com | tail -n +3", aStdout=_out),
                    exaMockCommand("/bin/virsh dumpxml .*"),
                    exaMockCommand("/bin/ln -s .*"),
                    exaMockCommand("/bin/test -e /sbin/brctl"),
                    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                    exaMockCommand("/sbin/ifup .*"),                    
                    exaMockCommand("/sbin/ifup .*"),                    
                    exaMockCommand("/sbin/ifup .*"),                    
                    exaMockCommand("/sbin/ifup .*"),
                    exaMockCommand("/bin/cp -f .*"),
                    exaMockCommand("ls *"),
                    exaMockCommand("ls *")
                ],
                [ 
                    exaMockCommand("vm_maker.*", aPersist=True),
                    exaMockCommand(".*mkdir.*"),
                    exaMockCommand(".*mount.*"),
                    exaMockCommand(".*cat.*", aRc=1),
                    exaMockCommand(".*echo.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand("/usr/sbin/nft .*"),                    
                    exaMockCommand("/usr/sbin/nft .*"),
                    exaMockCommand("/usr/bin/touch /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/under_migration")
                ],
                [
                    exaMockCommand("/usr/bin/mount .*"),
                    exaMockCommand("/usr/bin/mkdir .*"),
                    exaMockCommand("/bin/cat /etc/fstab .*")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        self.mGetContext().mSetConfigOption("exascale", {"vm_move_api": "oeda"})

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "move",
            "vm_name": "scaqab10client01vm08.us.oracle.com",
            "target_dom0_name": "scaqab10adm07.us.oracle.com",
            "source_dom0_name": "scaqab10adm01.us.oracle.com",
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
            "new_admin_mask": "255.255.0.0"
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch('exabox.ovm.cluexascale.ebGetDefaultDB', return_value=MagicMock()), \
             patch('exabox.ovm.clucontrol.mEnsureOedaJavaHome'), \
             patch('exabox.tools.ebOedacli.ebOedacli.mEnsureOedaJavaHome'), \
             patch.object(_exascale, 'mCreateLockObj', return_value=MagicMock()):
            _exascale.mPerformVmMove(_options)
        _exascale.mMountVolumesVmMove(_options)

    def test_vm_move_sanity_oeda_missing_payload(self):
        roce_information = None 
        _options = self.mGetPayload()
        if roce_information is None:
            roce_information = {}
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": "testvm",
            "roce_information": roce_information,
        }
        return _options

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_update_dom0_network_skip_commands(self, mock_oedacli, mock_tree):
        # Auto-generated test for mUpdateDom0Network skip branch
        _ebox = MagicMock()
        _ebox.mGetUUID.return_value = "uuid"
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mGetPatchConfig.return_value = "/patch/config.xml"
        _ebox.mGetOedaPath.return_value = "/oeda"
        _options = self._build_dom0_network_options()
        _ebox.mGetOptions.return_value = _options
        _exascale = ebCluExaScale(_ebox)

        _exascale.mUpdateDom0Network()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/12_before_dom0_net_update.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        mock_tree.assert_called_once_with("/patch/config.xml")
        mock_tree.return_value.mExportXml.assert_called_once_with(initial_xml)
        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        mock_oedacli.return_value.mAppendCommand.assert_not_called()
        mock_oedacli.return_value.mRun.assert_not_called()

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_update_dom0_network_append_commands(self, mock_oedacli, mock_tree):
        # Auto-generated test for mUpdateDom0Network command path
        _ebox = MagicMock()
        _ebox.isBaseDB.return_value = False
        _ebox.mGetUUID.return_value = "uuid"
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mGetPatchConfig.return_value = "/patch/config.xml"
        _ebox.mGetOedaPath.return_value = "/oeda"
        roce_info = {
            "dom0-1": {
                "stre0_ip": "10.0.0.1",
                "stre1_ip": "10.0.0.2",
                "subnet_mask": "255.255.255.0",
                "vlan_id": "100"
            }
        }
        _options = self._build_dom0_network_options(roce_info)
        _ebox.mGetOptions.return_value = _options
        _exascale = ebCluExaScale(_ebox)

        tree_initial = MagicMock()
        tree_update = MagicMock()
        mock_tree.side_effect = [tree_initial, tree_update]

        oedacli_instance = MagicMock()
        mock_oedacli.return_value = oedacli_instance

        _exascale.mUpdateDom0Network()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/12_before_dom0_net_update.xml"
        update_xml = f"{local_prefix}/13_after_dom0_net_update.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        self.assertEqual(mock_tree.call_args_list, [call("/patch/config.xml"), call(update_xml)])
        tree_initial.mExportXml.assert_called_once_with(initial_xml)
        tree_update.mExportXml.assert_called_once_with("/patch/config.xml")

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        expected_calls = [
            call("ALTER NETWORK", {"HOSTNAME": "dom0-1-priv1", "IP": "10.0.0.1", "NETMASK": "255.255.255.0", "VLANID": "100"}, {"ID": "dom0-1_priv1"}),
            call("ALTER NETWORK", {"HOSTNAME": "dom0-1-priv2", "IP": "10.0.0.2", "NETMASK": "255.255.255.0", "VLANID": "100"}, {"ID": "dom0-1_priv2"}),
        ]
        self.assertEqual(oedacli_instance.mAppendCommand.call_args_list, expected_calls)
        oedacli_instance.mRun.assert_called_once_with(initial_xml, update_xml)

# Auto-generated test for mPerformVmMoveSanityChecksOEDA
        _options = self._build_oeda_sanity_options()
        del _options.jsonconf["source_dom0_name"]

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x1, "invalid payload")

        with patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()
        self.assertEqual("INVALID_PAYLOAD", mock_fail.call_args[0][0])

    def test_vm_move_sanity_oeda_target_unreachable(self):
        # Auto-generated test for mPerformVmMoveSanityChecksOEDA target reachability branch
        _options = self._build_oeda_sanity_options()
        _cluctrl = Mock()
        _cluctrl.mPingHost.return_value = False

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x2, "target unreachable")

        with patch.object(ebCluExaScale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()

    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_vm_move_sanity_oeda_invalid_node_type(
        self,
        mock_exec_cmd_check,
        mock_connect,
        mock_get_gctx
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksOEDA invalid node type branch

        _options = self._build_oeda_sanity_options()
        _cluctrl = Mock()
        _cluctrl.mPingHost.return_value = True

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx


        _target_node = MagicMock(name="target_node")
        mock_connect.side_effect = [_make_ctx(_target_node)]
        mock_exec_cmd_check.return_value = SimpleNamespace(stdout='NOTKVM')

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x3, "invalid node type")

        with patch.object(_exascale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()
        self.assertEqual('INVALID_NODE_TYPE', mock_fail.call_args[0][0])
        self.assertEqual(
            {'type': 'NOTKVM', 'host': _options.jsonconf['target_dom0_name']},
            mock_fail.call_args[1]['aCausePlaceholders']
        )

    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_vm_move_sanity_oeda_invalid_hypervisor(
        self,
        mock_exec_cmd_check,
        mock_connect,
        mock_get_gctx
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksOEDA invalid hypervisor branch

        _options = self._build_oeda_sanity_options()
        _cluctrl = Mock()
        _cluctrl.mPingHost.return_value = True

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = MagicMock(name="target_node")
        mock_connect.side_effect = [_make_ctx(_target_node)]
        mock_exec_cmd_check.side_effect = [
            SimpleNamespace(stdout='KVMHOST'),
            Exception('virsh failure')
        ]

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x4, "invalid hypervisor")

        with patch.object(_exascale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()
        self.assertEqual('INVALID_HYPERVISOR', mock_fail.call_args[0][0])

    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_vm_move_sanity_oeda_vm_already_moved(
        self,
        mock_exec_cmd_check,
        mock_connect,
        mock_get_gctx
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksOEDA VM already moved branch

        _options = self._build_oeda_sanity_options()
        _vm_name = _options.jsonconf['vm_name']
        _cluctrl = Mock()
        _cluctrl.mPingHost.return_value = True

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = MagicMock(name="target_node")
        mock_connect.side_effect = [_make_ctx(_target_node)]
        mock_exec_cmd_check.side_effect = [
            SimpleNamespace(stdout='KVMHOST'),
            SimpleNamespace(stdout=f"{_vm_name}\n")
        ]

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x5, "already moved")

        with patch.object(_exascale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()
        self.assertEqual('VM_ALREADY_MOVED', mock_fail.call_args[0][0])

    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_vm_move_sanity_oeda_edv_services_offline(
        self,
        mock_exec_cmd_check,
        mock_connect,
        mock_get_gctx
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksOEDA EDV services offline branch

        _options = self._build_oeda_sanity_options()
        _cluctrl = Mock()
        _cluctrl.mPingHost.return_value = True

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = MagicMock(name="target_node")
        mock_connect.side_effect = [_make_ctx(_target_node)]
        mock_exec_cmd_check.side_effect = [
            SimpleNamespace(stdout='KVMHOST'),
            SimpleNamespace(stdout=''),
            SimpleNamespace(stdout='state: OFFLINE')
        ]

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x6, "EDV offline")

        with patch.object(_exascale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()
        self.assertEqual('EDV_SERVICES_OFFLINE', mock_fail.call_args[0][0])

    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.RemoteLock')
    @patch('exabox.ovm.cluexascale.get_node_bridges')
    @patch('exabox.ovm.cluexascale.get_kvm_guest_bridges')
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_vm_move_sanity_oeda_stale_vm_files(
        self,
        mock_exec_cmd_check,
        mock_connect,
        mock_exec_cmd,
        mock_guest_bridges,
        mock_get_bridges,
        mock_remote_lock,
        mock_get_gctx
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksOEDA stale VM files branch

        _options = self._build_oeda_sanity_options()
        _vm_name = _options.jsonconf['vm_name']
        _cluctrl = Mock()
        _cluctrl.mPingHost.return_value = True

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = MagicMock(name="target_node")
        _target_node.mFileExists.return_value = False  # ensure stale files are not treated as under migration
        mock_connect.side_effect = [_make_ctx(_target_node)]
        mock_exec_cmd_check.side_effect = [
            SimpleNamespace(stdout='KVMHOST'),
            SimpleNamespace(stdout=''),
            SimpleNamespace(stdout='state: ONLINE'),
            SimpleNamespace(stdout='stale_vm')
        ]

        stale_vm = 'stale_vm'
        mock_exec_cmd.return_value = SimpleNamespace(exit_code=0)
        mock_guest_bridges.return_value = ('vmeth0', None, set(), set())
        mock_get_bridges.return_value = [SimpleNamespace(name='vmeth0'), SimpleNamespace(name='vmeth205')]

        _exascale = ebCluExaScale(self.mGetClubox())

        def _raise_failure(*_args, **_kwargs):
            raise ExacloudRuntimeError(0x1000, 0x7, "stale vm files")

        with patch.object(_exascale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'fail', side_effect=_raise_failure) as mock_fail:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_called_once()
        self.assertEqual('STALE_VM_FILES', mock_fail.call_args[0][0])
        """
        mock_exec_cmd.assert_called_once_with(
            _target_node,
            f"/bin/ls /EXAVMIMAGES/GuestImages/{stale_vm}/vm*.xml"
        )
        """
        mock_remote_lock.assert_not_called()

    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    @patch('exabox.ovm.cluexascale.get_bond_monitor_installed', return_value=True)
    @patch('exabox.ovm.cluexascale.RemoteLock')
    @patch('exabox.ovm.cluexascale.get_node_bridges')
    @patch('exabox.ovm.cluexascale.get_kvm_guest_bridges')
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_vm_move_sanity_oeda_under_migration_files_not_stale(
        self,
        mock_exec_cmd_check,
        mock_connect,
        mock_exec_cmd,
        mock_guest_bridges,
        mock_get_bridges,
        mock_remote_lock,
        mock_bond_monitor,
        mock_get_gctx
    ):
        # Ensure files marked as under migration are ignored by stale check

        _options = self._build_oeda_sanity_options()
        _cluctrl = Mock()
        _cluctrl.mPingHost.side_effect = [True, False, False]

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = MagicMock(name="target_node")

        def _file_exists(path):
            if path.endswith('/under_migration'):
                return True
            return False

        _target_node.mFileExists.side_effect = _file_exists
        mock_connect.side_effect = [_make_ctx(_target_node)]
        mock_exec_cmd_check.side_effect = [
            SimpleNamespace(stdout='KVMHOST'),
            SimpleNamespace(stdout=''),
            SimpleNamespace(stdout='state: ONLINE'),
            SimpleNamespace(stdout='moving_vm')
        ]
        mock_exec_cmd.return_value = SimpleNamespace(exit_code=1)
        mock_guest_bridges.return_value = ('vmeth0', None, set(), set())
        mock_get_bridges.return_value = []

        _exascale = ebCluExaScale(self.mGetClubox())
        with patch.object(_exascale, 'mGetCluCtrl', return_value=_cluctrl), \
             patch.object(_exascale, 'mGetGcvDevicePath', return_value='gcv_device'), \
             patch.object(_exascale, 'fail') as mock_fail:
            _exascale.mPerformVmMoveSanityChecksOEDA(_options, {})

        mock_fail.assert_not_called()
        _target_node.mFileExists.assert_called()

    def test_vm_move_sanity_exacloud_missing_payload(self):
        # Auto-generated test for mPerformVmMoveSanityChecksExacloud missing payload branch
        _options = self._build_exacloud_sanity_options()
        del _options.jsonconf["source_dom0_name"]

        _exascale = ebCluExaScale(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMoveSanityChecksExacloud(_options)

        self.assertIn('Missing "source_dom0_name"', str(ctx.exception))

    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check', return_value="/bin/ls")
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.get_node_filesystems')
    @patch('exabox.ovm.cluexascale.node_read_text_file')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    def test_vm_move_sanity_exacloud_success(
        self,
        mock_get_gctx,
        mock_connect,
        mock_read_text,
        mock_get_fs,
        mock_exec_cmd_check,
        mock_exec_cmd,
        mock_cmd_abs_path
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksExacloud success path

        _options = self._build_exacloud_sanity_options()

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = Mock(name="target_node")
        _source_node = Mock(name="source_node")
        mock_connect.side_effect = [_make_ctx(_target_node), _make_ctx(_source_node)]

        mock_exec_cmd.return_value = (0, "/EXAVMIMAGES/dep1.zip\n/EXAVMIMAGES/dep2.zip\n", "")

        _disk_images = [
            "/EXAVMIMAGES/GuestImages/testvm/System.img",
            "/EXAVMIMAGES/GuestImages/testvm/Data.img"
        ]
        mock_exec_cmd_check.return_value = (0, "\n".join(_disk_images), "")

        mock_read_text.return_value = (
            "<domuVolume>/EXAVMIMAGES/dep1.zip</domuVolume>\n"
            "<domuVolume>/EXAVMIMAGES/dep2.zip</domuVolume>"
        )

        _target_fs = SimpleNamespace(mountpoint="/EXAVMIMAGES", free_bytes=800)
        _source_fs = SimpleNamespace(mountpoint="/EXAVMIMAGES", free_bytes=600)
        mock_get_fs.side_effect = [[_target_fs], [_source_fs]]

        _size_map = {
            _disk_images[0]: 120,
            _disk_images[1]: 80,
        }

        def _file_info(path):
            return SimpleNamespace(st_size=_size_map[path])

        _source_node.mGetFileInfo.side_effect = _file_info

        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mPerformVmMoveSanityChecksExacloud(_options)

        self.assertEqual(mock_connect.call_count, 2)
        _seen = [call.args[0] for call in _source_node.mGetFileInfo.call_args_list]
        self.assertCountEqual(_disk_images, _seen)

    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check', return_value="/bin/ls")
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.get_node_filesystems')
    @patch('exabox.ovm.cluexascale.node_read_text_file')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    def test_vm_move_sanity_exacloud_source_space_failure(
        self,
        mock_get_gctx,
        mock_connect,
        mock_read_text,
        mock_get_fs,
        mock_exec_cmd_check,
        mock_exec_cmd,
        mock_cmd_abs_path
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksExacloud source free space branch

        _options = self._build_exacloud_sanity_options()

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = Mock(name="target_node")
        _source_node = Mock(name="source_node")
        mock_connect.side_effect = [_make_ctx(_target_node), _make_ctx(_source_node)]

        mock_exec_cmd.return_value = (0, "/EXAVMIMAGES/dep1.zip\n", "")

        _disk_images = [
            "/EXAVMIMAGES/GuestImages/testvm/System.img",
            "/EXAVMIMAGES/GuestImages/testvm/Data.img"
        ]
        mock_exec_cmd_check.return_value = (0, "\n".join(_disk_images), "")

        mock_read_text.return_value = (
            "<domuVolume>/EXAVMIMAGES/dep1.zip</domuVolume>\n"
            "<domuVolume>/EXAVMIMAGES/dep2.zip</domuVolume>"
        )

        _target_fs = SimpleNamespace(mountpoint="/EXAVMIMAGES", free_bytes=900)
        _source_fs = SimpleNamespace(mountpoint="/EXAVMIMAGES", free_bytes=150)
        mock_get_fs.side_effect = [[_target_fs], [_source_fs]]

        _size_map = {
            _disk_images[0]: 200,
            _disk_images[1]: 150,
            "/EXAVMIMAGES/dep2.zip": 100,
        }

        def _file_info(path):
            return SimpleNamespace(st_size=_size_map[path])

        _source_node.mGetFileInfo.side_effect = _file_info

        _exascale = ebCluExaScale(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMoveSanityChecksExacloud(_options)

        self.assertIn("can't hold the compressed DomU", str(ctx.exception))

    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check', return_value="/bin/ls")
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.get_node_filesystems')
    @patch('exabox.ovm.cluexascale.node_read_text_file')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    def test_vm_move_sanity_exacloud_target_space_failure(
        self,
        mock_get_gctx,
        mock_connect,
        mock_read_text,
        mock_get_fs,
        mock_exec_cmd_check,
        mock_exec_cmd,
        mock_cmd_abs_path
    ):
        # Auto-generated test for mPerformVmMoveSanityChecksExacloud target space branch

        _options = self._build_exacloud_sanity_options()

        def _make_ctx(node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = node
            _ctx.__exit__.return_value = False
            return _ctx

        _target_node = Mock(name="target_node")
        _source_node = Mock(name="source_node")
        mock_connect.side_effect = [_make_ctx(_target_node), _make_ctx(_source_node)]

        mock_exec_cmd.return_value = (0, "/EXAVMIMAGES/dep1.zip\n", "")

        _disk_images = [
            "/EXAVMIMAGES/GuestImages/testvm/System.img",
            "/EXAVMIMAGES/GuestImages/testvm/Data.img"
        ]
        mock_exec_cmd_check.return_value = (0, "\n".join(_disk_images), "")

        mock_read_text.return_value = (
            "<domuVolume>/EXAVMIMAGES/dep1.zip</domuVolume>\n"
            "<domuVolume>/EXAVMIMAGES/dep2.zip</domuVolume>"
        )

        _target_fs = SimpleNamespace(mountpoint="/EXAVMIMAGES", free_bytes=200)
        _source_fs = SimpleNamespace(mountpoint="/EXAVMIMAGES", free_bytes=600)
        mock_get_fs.side_effect = [[_target_fs], [_source_fs]]

        _size_map = {
            _disk_images[0]: 120,
            _disk_images[1]: 80,
            "/EXAVMIMAGES/dep2.zip": 60,
        }

        def _file_info(path):
            return SimpleNamespace(st_size=_size_map[path])

        _source_node.mGetFileInfo.side_effect = _file_info

        _exascale = ebCluExaScale(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMoveSanityChecksExacloud(_options)

        self.assertIn("does not have enough space", str(ctx.exception))

    def test_mperformvmmove_requires_exascale(self):
        # Auto-generated test for mPerformVmMove non-exascale branch
        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = False
        _options = SimpleNamespace(jsonconf={'action': 'move'}, undo='false')
        _exascale = ebCluExaScale(_cluctrl)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMove(_options)

        self.assertIn('Operation allowed only in ExaScale', str(ctx.exception))

    def test_mperformvmmove_missing_payload(self):
        # Auto-generated test for mPerformVmMove missing payload branch
        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _options = SimpleNamespace(jsonconf=None, undo='false')
        _exascale = ebCluExaScale(_cluctrl)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMove(_options)

        self.assertIn('Missing JSON Payload required for VM move', str(ctx.exception))

    def test_mperformvmmove_missing_action(self):
        # Auto-generated test for mPerformVmMove missing action branch
        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _options = SimpleNamespace(jsonconf={}, undo='false')
        _exascale = ebCluExaScale(_cluctrl)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMove(_options)

        self.assertIn('Missing "action" field in JSON payload', str(ctx.exception))

    @patch('exabox.ovm.cluexascale.csUtil')
    @patch.object(ebCluExaScale, 'mPerformVmMoveSanityChecksOEDA')
    @patch.object(ebCluExaScale, 'mCreateLockObj')
    def test_mperformvmmove_sanity_default_oeda(self, mock_create_lock, mock_sanity_oeda, mock_csutil):
        # Auto-generated test for mPerformVmMove default OEDA sanity path
        _options = SimpleNamespace(
            jsonconf={
                'action': 'moveSanityCheck',
                'vm_name': 'vm01',
                'target_dom0_name': 'dom0-target',
                'source_dom0_name': 'dom0-source'
            },
            undo='false'
        )

        _lock = MagicMock()
        mock_create_lock.return_value = _lock
        mock_csutil.return_value.mDeleteStaleDummyBridge.return_value = None

        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _cluctrl.mCheckConfigOption.return_value = None

        _exascale = ebCluExaScale(_cluctrl)

        _exascale.mPerformVmMove(_options)

        mock_create_lock.assert_called_once_with(_options)
        _lock.acquire.assert_called_once()
        _lock.release.assert_called_once()
        mock_csutil.return_value.mDeleteStaleDummyBridge.assert_not_called()
        mock_sanity_oeda.assert_called_once_with(_options, None)

    @patch.object(ebCluExaScale, 'mPerformVmMoveSanityChecksExacloud')
    def test_mperformvmmove_sanity_exacloud(self, mock_sanity_exacloud):
        # Auto-generated test for mPerformVmMove Exacloud sanity path
        _options = SimpleNamespace(
            jsonconf={
                'action': 'moveSanityCheck',
                'vm_name': 'vm02',
                'target_dom0_name': 'dom0-target',
                'source_dom0_name': 'dom0-source'
            },
            undo='false'
        )

        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _cluctrl.mCheckConfigOption.return_value = {'vm_move_api': 'exacloud'}

        _exascale = ebCluExaScale(_cluctrl)

        _exascale.mPerformVmMove(_options)

        mock_sanity_exacloud.assert_called_once_with(_options)

    def test_mperformvmmove_unknown_api(self):
        # Auto-generated test for mPerformVmMove unknown API branch
        _options = SimpleNamespace(
            jsonconf={
                'action': 'move',
                'vm_name': 'vm03',
                'target_dom0_name': 'dom0-target',
                'source_dom0_name': 'dom0-source'
            },
            undo='false'
        )

        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _cluctrl.mCheckConfigOption.return_value = {'vm_move_api': 'unknown'}
        _cluctrl.mDom0UpdateCurrentOpLog = MagicMock()

        _exascale = ebCluExaScale(_cluctrl)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMove(_options)

        self.assertIn('Unknown VM move API', str(ctx.exception))

    @patch('exabox.ovm.cluexascale.ebLogWarn')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch.object(ebCluExaScale, 'mCreateLockObj')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=MagicMock(name="gctx"))
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    def test_cleanup_vm_move_removes_bridges(
        self,
        mock_exec_cmd,
        mock_get_gctx,
        mock_create_lock,
        mock_connect,
        mock_log_warn
    ):
        # Auto-generated test for mCleanUpVMMove bridge removal branch
        _options = SimpleNamespace(
            jsonconf={
                'vm_name': 'vm-clean',
                'target_dom0_name': 'dom0-target',
                'source_dom0_name': 'dom0-source',
                'new_admin_hostname': 'new-host',
                'new_admin_domainname': 'example.com'
            }
        )

        _lock = MagicMock()
        mock_create_lock.return_value = _lock

        _machine_config = MagicMock()
        _machine_config.mGetMacNetworks.return_value = ['net-client', 'net-backup']

        _client_conf = MagicMock()
        _client_conf.mGetNetType.return_value = 'client'
        _client_conf.mGetNetVlanId.return_value = '123'

        _backup_conf = MagicMock()
        _backup_conf.mGetNetType.return_value = 'backup'
        _backup_conf.mGetNetVlanId.return_value = '456'

        _networks = MagicMock()
        _networks.mGetNetworkConfig.side_effect = [_client_conf, _backup_conf]

        _machines = MagicMock()
        _machines.mGetMachineConfig.return_value = _machine_config

        _cluctrl = MagicMock()
        _cluctrl.mGetMachines.return_value = _machines
        _cluctrl.mGetNetworks.return_value = _networks

        _ctx_node = MagicMock(name="source_node")

        def _make_ctx(_node):
            _ctx = MagicMock()
            _ctx.__enter__.return_value = _node
            _ctx.__exit__.return_value = False
            return _ctx

        mock_connect.side_effect = [_make_ctx(_ctx_node)]

        _exascale = ebCluExaScale(_cluctrl)

        _exascale.mCleanUpVMMove(_options)

        mock_create_lock.assert_called_once_with(_options)
        _lock.acquire.assert_called_once()
        _lock.release.assert_called_once()
        mock_log_warn.assert_not_called()
        expected_calls = [
            call(_ctx_node, f"{VM_MAKER} --remove-bridge vmbondeth0.123"),
            call(_ctx_node, f"{VM_MAKER} --remove-bridge vmbondeth0.456")
        ]
        mock_exec_cmd.assert_has_calls(expected_calls, any_order=True)

    @patch('exabox.ovm.cluexascale.ebLogWarn')
    @patch('exabox.ovm.cluexascale.get_kvm_guest_bridges',
           return_value=['vmbondeth0.123'])
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch.object(ebCluExaScale, 'mCreateLockObj')
    @patch('exabox.ovm.cluexascale.get_gcontext',
           return_value=MagicMock(name="gctx"))
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.node_exec_cmd')
    def test_cleanup_vm_move_force_removes_vm_with_vm_maker(
        self,
        mock_exec_cmd,
        mock_exec_cmd_check,
        mock_get_gctx,
        mock_create_lock,
        mock_connect,
        mock_get_bridges,
        mock_log_warn
    ):
        _options = SimpleNamespace(
            jsonconf={
                'vm_name': 'vm-clean',
                'target_dom0_name': 'dom0-target',
                'source_dom0_name': 'dom0-source',
                'new_admin_hostname': 'new-host',
                'new_admin_domainname': 'example.com',
                'force': 'true'
            }
        )

        _lock = MagicMock()
        mock_create_lock.return_value = _lock

        _machine_config = MagicMock()
        _machine_config.mGetMacNetworks.return_value = []

        _machines = MagicMock()
        _machines.mGetMachineConfig.return_value = _machine_config

        _cluctrl = MagicMock()
        _cluctrl.mGetMachines.return_value = _machines
        _cluctrl.mGetNetworks.return_value = MagicMock()
        _cluctrl.mPingHost.return_value = True

        _ctx_node = MagicMock(name="source_node")
        _ctx = MagicMock()
        _ctx.__enter__.return_value = _ctx_node
        _ctx.__exit__.return_value = False
        mock_connect.return_value = _ctx

        mock_exec_cmd_check.return_value = SimpleNamespace(stdout='vm-clean\n')
        mock_exec_cmd.return_value = SimpleNamespace(stdout='serial123\n',
                                                     exit_code=0)

        _exascale = ebCluExaScale(_cluctrl)

        _exascale.mCleanUpVMMove(_options)

        mock_create_lock.assert_called_once_with(_options)
        _lock.acquire.assert_called_once()
        _lock.release.assert_called_once()
        mock_log_warn.assert_not_called()
        mock_get_bridges.assert_called_once_with(_ctx_node, 'vm-clean')

        _commands = [args[1] for args, _kwargs in mock_exec_cmd.call_args_list]
        self.assertIn('/bin/rm -rf /EXAVMIMAGES/console/serial123',
                      _commands)
        self.assertIn(f"{VM_MAKER} --stop-domain vm-clean --destroy",
                      _commands)
        self.assertIn(f"{VM_MAKER} --remove-domain vm-clean", _commands)
        self.assertIn(f"{VM_MAKER} --remove-bridge vmbondeth0.123",
                      _commands)
        self.assertNotIn('/bin/virsh destroy vm-clean', _commands)
        self.assertNotIn('/bin/virsh undefine vm-clean', _commands)

    @patch('exabox.ovm.cluexascale.ebLogWarn')
    @patch.object(ebCluExaScale, 'mCreateLockObj')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=MagicMock(name="gctx"))
    def test_cleanup_vm_move_force_skips_unreachable(
        self,
        mock_get_gctx,
        mock_connect,
        mock_create_lock,
        mock_log_warn
    ):
        # Auto-generated test for mCleanUpVMMove force unreachable branch
        _options = SimpleNamespace(
            jsonconf={
                'vm_name': 'vm-clean',
                'target_dom0_name': 'dom0-target',
                'source_dom0_name': 'dom0-source',
                'new_admin_hostname': 'new-host',
                'new_admin_domainname': 'example.com',
                'force': 'true'
            }
        )

        _lock = MagicMock()
        mock_create_lock.return_value = _lock

        _machine_config = MagicMock()
        _machine_config.mGetMacNetworks.return_value = []

        _machines = MagicMock()
        _machines.mGetMachineConfig.return_value = _machine_config

        _cluctrl = MagicMock()
        _cluctrl.mGetMachines.return_value = _machines
        _cluctrl.mGetNetworks.return_value = MagicMock()
        _cluctrl.mPingHost.return_value = False

        _exascale = ebCluExaScale(_cluctrl)

        _exascale.mCleanUpVMMove(_options)

        mock_create_lock.assert_called_once_with(_options)
        _lock.acquire.assert_called_once()
        _lock.release.assert_called_once()
        mock_log_warn.assert_called_once()
        mock_connect.assert_not_called()

    def test_mperformvmmoveoeda_missing_field(self):
        # Auto-generated test for mPerformVmMoveOEDA payload validation branch
        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _options = SimpleNamespace(jsonconf={'vm_name': 'vm'}, undo='false')
        _exascale = ebCluExaScale(_cluctrl)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMoveOEDA(_options)

        self.assertIn('Missing "target_dom0_name" in ExaScale Payload', str(ctx.exception))

    def test_mperformvmmoveexacloud_missing_field(self):
        # Auto-generated test for mPerformVmMoveExacloud payload validation branch
        _cluctrl = MagicMock()
        _cluctrl.mIsExaScale.return_value = True
        _options = SimpleNamespace(jsonconf={'vm_name': 'vm'}, undo='false')
        _exascale = ebCluExaScale(_cluctrl)

        with self.assertRaises(ExacloudRuntimeError) as ctx:
            _exascale.mPerformVmMoveExacloud(_options)

        self.assertIn('Missing "target_dom0_name" in ExaScale Payload', str(ctx.exception))

    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPostVMMoveSteps")
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mProbePath", return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('socket.gethostbyname', return_value="localhost")
    def test_003_vm_move_prepare_oeda(self, mock_mPostVMMoveSteps, mock_mRun, mock_mProbePath, mock_mDom0UpdateCurrentOpLog, mock_socket):

        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*chmod.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*stage.*", ebTestClucontrol.mRealExecute),
                    exaMockCommand(".*ping.*", aRc=1, aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*umount.*"),
                    exaMockCommand(".*rmdir.*"),
                    exaMockCommand(".*sed.*"),
                    exaMockCommand(".*mount.*"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        self.mGetContext().mSetConfigOption("exascale", {"vm_move_api": "oeda"})

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "move",
            "vm_name": "scaqab10client01vm08.us.oracle.com",
            "target_dom0_name": "scaqab10adm07.us.oracle.com",
            "source_dom0_name": "scaqab10adm01.us.oracle.com",
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
            "new_admin_mask": "255.255.0.0"
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch('exabox.ovm.cluexascale.ebGetDefaultDB', return_value=MagicMock()), \
             patch.object(_exascale, 'mCreateLockObj', return_value=MagicMock()):
            _exascale.mPrepareVmMoveOEDA(_options)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('socket.gethostbyname', return_value="localhost")
    def test_004_vm_move_prechecks_exacloud(self, mock_mDom0UpdateCurrentOpLog, mock_socket):

        _sourceDom0 = "scaqab10adm01.us.oracle.com"
        _targetDom0 = "scaqab10adm07.us.oracle.com"
        _vmName = "scaqab10adm01vm08.us.oracle.com"
        #Mock commands
        _cmds = {
            _sourceDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/*.zip"), aStdout="/EXAVMIMAGES/test.zip"),
                    exaMockCommand("/bin/test -e /bin/df"),
                    exaMockCommand("/bin/test -e /bin/grep"),
                    exaMockCommand("/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'", aStdout=(
                        "Mounted on   Filesystem   Type   1B-blocks   Avail\n"
                        "/EXAVMIMAGES /dev/sda     ext4   2048        1024")),
                    exaMockCommand(f"/bin/cat /EXAVMIMAGES/conf/{_vmName}-vm.xml",
                                   aStdout="<domuVolume>/EXAVMIMAGES/test2.zip</domuVolume>"),
                    exaMockCommand(re.escape(f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}/*.img"),
                                   aStdout=f"/EXAVMIMAGES/GuestImages/{_vmName}/System.img"),
                    exaMockCommand(f"/bin/stat /EXAVMIMAGES/GuestImages/{_vmName}/System.img",
                                   aStdout="Size: 64"),
                    exaMockCommand("/bin/stat /EXAVMIMAGES/test2.zip", aStdout="Size: 32"),
                    exaMockCommand("/bin/test -e /bin/lsblk", aPersist=True),
                    exaMockCommand("/bin/lsblk -rno TYPE /dev/sda"),
                ]
            ],
            _targetDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/*.zip"), aStdout="/EXAVMIMAGES/test3.zip"),
                    exaMockCommand("/bin/test -e /bin/df"),
                    exaMockCommand("/bin/test -e /bin/grep"),
                    exaMockCommand("/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'", aStdout=(
                        "Mounted on   Filesystem   Type   1B-blocks   Avail\n"
                        "/EXAVMIMAGES /dev/sda     ext4   1024        512")),
                    exaMockCommand("/bin/test -e /bin/lsblk", aPersist=True),
                    exaMockCommand("/bin/lsblk -rno TYPE /dev/sda"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": _vmName,
            "target_dom0_name": _targetDom0,
            "source_dom0_name": _sourceDom0,
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption",
                   return_value={"vm_move_api": "exacloud"}):
            _exascale.mPerformVmMove(_options)


    @patch.object(ebCluExaScale, 'mCreateLockObj')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')
    @patch('socket.gethostbyname', return_value="localhost")
    def test_005_vm_move_prechecks_oeda(self, mock_mDom0UpdateCurrentOpLog, mock_mCreateLockObj, mock_socket):

        _sourceDom0 = "scaqab10adm01.us.oracle.com"
        _targetDom0 = "scaqab10adm07.us.oracle.com"
        _vmName = "scaqab10adm01vm08.us.oracle.com"

        _tgtVMBridges = (
            " Interface   Type      Source            Model     MAC\n"
            "----------------------------------------------------------------------\n"
            " -           bridge    vmbondeth0.1239   virtio    00:00:17:01:bc:70\n"
            " -           bridge    vmbondeth0.1240   virtio    00:00:17:01:1a:7c\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:81:5f:4f\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:46:5b:ee\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:90:73:b4\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:53:a7:50\n"
            " -           bridge    vmeth205          virtio    52:54:00:6e:97:ee\n"
        )
        _tgtHostBridges = (
            "bridge name     bridge id               STP enabled     interfaces\n"
            "vmbondeth0\t              8000.b8cef67104a0       no              bondeth0\n"
            "vmbondeth0.1239\t         8000.b8cef67104a0       no              bondeth0.1239\n"
            "vmbondeth0.1240\t         8000.b8cef67104a0       no              bondeth0.1240\n"
            "vmeth0\t          8000.001b21e7b71d       no              eth0\n"
            "vmeth0.102\t              8000.001b21e7b71d       no              eth0.102\n"
            "vmeth205\t                8000.2ea3253eabe0       no              eth205\n"
        )
        _tgtHostVMBridges = (
            "vmbondeth0.1239\n"
            "vmbondeth0.1240\n"
        )
        _tgtFSs = (
            "Mounted on                                                                   Filesystem                  Type  1B-blocks      Avail\n"
            "/EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com /dev/exc/gcv_Vmrievh_1_e00a xfs  2042626048 1990975488\n"
        )

        #Mock commands
        _cmds = {
            _targetDom0: [
                #[
                #    exaMockCommand("/bin/test -e /bin/rmdir"),
                #    exaMockCommand("/bin/test -e /bin/df"),
                #    exaMockCommand("/bin/test -e /bin/lsblk"),
                #    exaMockCommand("/bin/test -e /bin/grep"),
                #    exaMockCommand(re.escape("/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'"), aStdout=_tgtFSs),
                #    exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vmrievh_1_e00a", aStdout="disk"),
                #    exaMockCommand("/bin/test -e /bin/virsh"),
                #    exaMockCommand("/bin/virsh list --all --name"),
                #    exaMockCommand("/bin/test -e /bin/umount"),
                #    exaMockCommand("/bin/test -e /bin/sed"),
                #    exaMockCommand("/bin/umount /EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com"),
                #    exaMockCommand(re.escape("/bin/sed -i '\\@/EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com@d' /etc/fstab")),
                #    exaMockCommand("/bin/rmdir /EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com"),
                #    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                #    exaMockCommand(re.escape("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*.xml |  /bin/sed 's/.*<source bridge=\\(.*\\)\\/>.*/\\1/' | /bin/tr -d \"\\'\" | /bin/tr -d \"\\\"\""), aStdout=_tgtHostVMBridges),
                #    exaMockCommand("test.*pgrep", aRc=0,),
                #    exaMockCommand("test.*grep", aRc=0,),
                #    exaMockCommand("/sbin/pgrep -af 'vm_maker.*' | /sbin/grep -v $$", aRc=0, aStdout="",),
                #],
                #[
                #    exaMockCommand(re.escape("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*.xml |  /bin/sed 's/.*<source bridge=\\(.*\\)\\/>.*/\\1/' | /bin/tr -d \"\\'\" | /bin/tr -d \"\\\"\""), aStdout=_tgtHostVMBridges),
                #    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                #    exaMockCommand("/bin/test -e /bin/grep"),
                #    exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"), aRc=1),
                #    exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge vmeth205"),
                #    exaMockCommand("/usr/sbin/vm_maker --list-domains"),
                #    exaMockCommand(re.escape("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*bondeth*")),
                #    exaMockCommand(re.escape("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*bondeth*"))
                #],
                [
                    exaMockCommand("/usr/local/bin/imageinfo --node-type", aStdout="KVMHOST"),
                    exaMockCommand("/bin/virsh list --all --name", aStdout="dummy.us.oracle.com"),
                    exaMockCommand("/sbin/edvutil lsedvnode | /bin/grep state", aStdout="state: ONLINE"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout="dummy.us.oracle.com"),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/GuestImages/dummy.us.oracle.com/under_migration", aRc=1),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/GuestImages/dummy.us.oracle.com/vm*.xml")),
                    exaMockCommand("/bin/ls /dev/exc/gcv_Vm1234_1_abcd", aRc=1),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domiflist dummy.us.oracle.com", aStdout=_tgtVMBridges),
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /etc/sysconfig/network-scripts/ifcfg-vmeth0*:205"),
                        aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0.102:205"),
                    exaMockCommand("/bin/test -e /sbin/brctl"),
                    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                    exaMockCommand("/bin/rpm -q bondmonitor", aStdout="bondmonitor"),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/GuestImages/dummy.us.oracle.com/snapshots")
                ]
            ],
            _sourceDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domiflist scaqab10adm01vm08.us.oracle.com", aStdout=_tgtVMBridges),
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /etc/sysconfig/network-scripts/ifcfg-vmeth0*:205"),
                        aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0.102:205"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/vmbondeth0.1239.xml"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/vmbondeth0.1240.xml"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/scaqab10adm01vm08.us.oracle.com.xml"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/vmeth*.xml")),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm07.us.oracle.com"),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01.us.oracle.com"),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01.us.oracle.com"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _lock = MagicMock()
        mock_mCreateLockObj.return_value = _lock

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": _vmName,            
            "target_dom0_name": _targetDom0,
            "source_dom0_name": _sourceDom0,
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch("exabox.ovm.cluexascale.ebCluExaScale.mGetGcvDevicePath",
                   return_value="gcv_Vm1234_1_abcd"):
            _exascale.mPerformVmMove(_options)

    def test_validate_volumes_positive(self):

        _volume_device_attached_vm = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/u01_Vm53942_1_8044\n"
        )

        self.mGetContext().mSetConfigOption('enable_validate_volumes', "True")

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com", aStdout=_volume_device_attached_vm),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client02vm08.us.oracle.com", aStdout=_volume_device_attached_vm), 
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "system_Vm53942_1_9044",
        }

        _clucommandhandler = CommandHandler(self.mGetClubox())

        ebLogInfo("Running success scenario where we are checking a specific volume is attached to the domU")
        _clucommandhandler.mHandlerValidateVolumes(_options)

         #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "",
        }

        ebLogInfo("Running success scenario where we are checking for the all the volumes to be attached to the domU")
        _clucommandhandler.mHandlerValidateVolumes(_options)

    def test_validate_volumes_negative_01(self):

        _volume_device_attached_vm = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/gcv_Vm53942_1_b60b\n"
            "Block /dev/exc/u01_Vm53942_1_8044\n"
        )

        self.mGetContext().mSetConfigOption('enable_validate_volumes', "True")

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com", aStdout=_volume_device_attached_vm),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "system_Vm53942_1_9047",
        }

        _clucommandhandler = CommandHandler(self.mGetClubox())

        ebLogInfo("Running failure scenario where we are checking a specific volume is not attached to the domU")
        with self.assertRaises(ExacloudRuntimeError):
            _clucommandhandler.mHandlerValidateVolumes(_options)

    def test_validate_volumes_negative_02(self):

        _volume_device_attached_vm_wrong = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/gcv_Vm53942_1_b60b\n"
            "Block /dev/exc/u01_Vm53942_1_8040\n"
        )

        self.mGetContext().mSetConfigOption('enable_validate_volumes', "True")

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com", aStdout=_volume_device_attached_vm_wrong),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "",
        }
        
        _clucommandhandler = CommandHandler(self.mGetClubox())

        ebLogInfo("Running failure scenario where we are checking for the all the volumes to be attached to the domU")
        with self.assertRaises(ExacloudRuntimeError):
            _clucommandhandler.mHandlerValidateVolumes(_options)

    def test_validate_volumes_disabled(self):

        _dom0 = "scaqab10adm01.us.oracle.com"
        _domU = "scaqab10client01vm08.us.oracle.com"
        _edvVolume = "system_Vm53942_1_9047"

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "",
            "edvvolume": "",
        }

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        
        self.mGetContext().mSetConfigOption('enable_validate_volumes', "False")
        _clucommandhandler = CommandHandler(self.mGetClubox())
        _clucommandhandler.mHandlerValidateVolumes(_options)
        

    @patch('exabox.ovm.cluexascale.get_gcontext')
    @patch('exabox.ovm.cluexascale.ebGetDefaultDB')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_roce_dom0_check_success(self, mock_connect, mock_get_db, mock_get_context):
        # Auto-generated test for mCheckDom0Roce
        mock_get_context.return_value = MagicMock()

        _options = type('Args', (), {})()
        _options.jsonconf = {
            'roce_config_dom0_name': 'scaqab10adm01.us.oracle.com',
        }

        _node = MagicMock()
        _node.mGetCmdExitStatus.side_effect = [0, 0]
        _context = MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = False
        mock_connect.return_value = _context

        request = MagicMock()
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        with patch.object(self.mGetClubox(), 'mGetRequestObj', return_value=request):
            _exascale = ebCluExaScale(self.mGetClubox())
            _ret = _exascale.mCheckDom0Roce(_options)

        self.assertEqual(_ret, 0)
        expected_cmds = [
            '/usr/sbin/ip a s stre0 | grep inet',
            '/usr/sbin/ip a s stre1 | grep inet',
        ]
        executed_cmds = [call.args[0] for call in _node.mExecuteCmdLog.call_args_list]
        self.assertEqual(executed_cmds, expected_cmds)

        request.mSetData.assert_called_once()
        payload = json.loads(request.mSetData.call_args[0][0])
        self.assertTrue(payload['roce_dom0_configured'])
        mock_db.mUpdateRequest.assert_called_once_with(request)

    @patch('exabox.ovm.cluexascale.get_gcontext')
    @patch('exabox.ovm.cluexascale.ebGetDefaultDB')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_roce_dom0_check_partial_failure(self, mock_connect, mock_get_db, mock_get_context):
        # Auto-generated test for mCheckDom0Roce
        mock_get_context.return_value = MagicMock()

        _options = type('Args', (), {})()
        _options.jsonconf = {
            'roce_config_dom0_name': 'scaqab10adm02.us.oracle.com',
        }

        _node = MagicMock()
        _node.mGetCmdExitStatus.side_effect = [0, 1]
        _context = MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = False
        mock_connect.return_value = _context

        request = MagicMock()
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        with patch.object(self.mGetClubox(), 'mGetRequestObj', return_value=request):
            _exascale = ebCluExaScale(self.mGetClubox())
            _ret = _exascale.mCheckDom0Roce(_options)

        self.assertEqual(_ret, 0)
        executed_cmds = [call.args[0] for call in _node.mExecuteCmdLog.call_args_list]
        self.assertEqual(executed_cmds, [
            '/usr/sbin/ip a s stre0 | grep inet',
            '/usr/sbin/ip a s stre1 | grep inet',
        ])

        request.mSetData.assert_called_once()
        payload = json.loads(request.mSetData.call_args[0][0])
        self.assertFalse(payload['roce_dom0_configured'])
        mock_db.mUpdateRequest.assert_called_once_with(request)

    def test_roce_dom0_check_missing_payload(self):
        # Auto-generated test for mCheckDom0Roce
        _options = type('Args', (), {})()
        _options.jsonconf = {}
        _exascale = ebCluExaScale(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError):
            _exascale.mCheckDom0Roce(_options)

    @patch('exabox.ovm.cluexascale.get_gcontext')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_roce_dom0_configure_success(self, mock_connect, mock_get_context):
        # Auto-generated test for mConfigureDom0Roce
        mock_get_context.return_value = MagicMock()

        _options = type('Args', (), {})()
        _options.jsonconf = {
            'roce_config_dom0_name': 'scaqab10adm03.us.oracle.com',
            'stre0_ip': '10.10.10.10',
        }

        _setup_node = MagicMock()
        _setup_node.mGetCmdExitStatus.return_value = 0
        _verify_node = MagicMock()
        _verify_node.mGetCmdExitStatus.side_effect = [0, 0]

        def _ctx(node):
            ctx = MagicMock()
            ctx.__enter__.return_value = node
            ctx.__exit__.return_value = False
            return ctx

        mock_connect.side_effect = [_ctx(_setup_node), _ctx(_verify_node)]

        with patch.object(self.mGetClubox(), 'mCheckConfigOption', side_effect=['1234', '255.255.1.0']):
            with patch.object(self.mGetClubox(), 'mRebootNode') as mock_reboot:
                _exascale = ebCluExaScale(self.mGetClubox())
                _ret = _exascale.mConfigureDom0Roce(_options)

                self.assertEqual(_ret, 0)
                mock_reboot.assert_called_once_with('scaqab10adm03.us.oracle.com')

        _setup_node.mExecuteCmdLog.assert_called_once_with('/usr/sbin/vm_maker --set --storage-vlan 1234 --ip 10.10.10.10 --netmask 255.255.1.0')
        executed_cmds = [call.args[0] for call in _verify_node.mExecuteCmdLog.call_args_list]
        self.assertEqual(executed_cmds, [
            '/usr/sbin/ip a s stre0 | grep 10.10.10.10',
            '/usr/sbin/ip a s stre1 | grep inet',
        ])

    @patch('exabox.ovm.cluexascale.get_gcontext')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_roce_dom0_configure_interface_failure(self, mock_connect, mock_get_context):
        # Auto-generated test for mConfigureDom0Roce
        mock_get_context.return_value = MagicMock()

        _options = type('Args', (), {})()
        _options.jsonconf = {
            'roce_config_dom0_name': 'scaqab10adm04.us.oracle.com',
            'stre0_ip': '10.20.20.20',
        }

        _setup_node = MagicMock()
        _setup_node.mGetCmdExitStatus.return_value = 0
        _verify_node = MagicMock()
        _verify_node.mGetCmdExitStatus.side_effect = [1]

        def _ctx(node):
            ctx = MagicMock()
            ctx.__enter__.return_value = node
            ctx.__exit__.return_value = False
            return ctx

        mock_connect.side_effect = [_ctx(_setup_node), _ctx(_verify_node)]

        with patch.object(self.mGetClubox(), 'mCheckConfigOption', side_effect=['1234', '255.255.0.0']):
            with patch.object(self.mGetClubox(), 'mRebootNode') as mock_reboot:
                _exascale = ebCluExaScale(self.mGetClubox())
                with self.assertRaises(ExacloudRuntimeError):
                    _exascale.mConfigureDom0Roce(_options)
                mock_reboot.assert_called_once_with('scaqab10adm04.us.oracle.com')

        executed_cmds = [call.args[0] for call in _verify_node.mExecuteCmdLog.call_args_list]
        self.assertEqual(executed_cmds, ['/usr/sbin/ip a s stre0 | grep 10.20.20.20'])

    def test_roce_dom0_configure_missing_payload(self):
        # Auto-generated test for mConfigureDom0Roce
        _options = type('Args', (), {})()
        _options.jsonconf = {
            'roce_config_dom0_name': 'scaqab10adm05.us.oracle.com',
        }
        _exascale = ebCluExaScale(self.mGetClubox())
        with self.assertRaises(ExacloudRuntimeError):
            _exascale.mConfigureDom0Roce(_options)

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_update_volumes_oedacli_skip(self, mock_oedacli, mock_tree):
        # Auto-generated test for mUpdateVolumesOedacli skip branch
        _ebox, _ = self._build_volume_ebox(config_overrides={"exascale_edv_enable": ""})
        _exascale = ebCluExaScale(_ebox)

        _exascale.mUpdateVolumesOedacli()

        mock_tree.assert_not_called()
        mock_oedacli.assert_not_called()
        _ebox.mExecuteLocal.assert_not_called()

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_update_volumes_oedacli_cs_standard(self, mock_oedacli, mock_tree):
        # Auto-generated test for mUpdateVolumesOedacli command path
        jsonconf = {
            "customer_network": {
                "nodes": [
                    {
                        "client": {
                            "hostname": "host1",
                            "domainname": "example.com",
                            "dom0_oracle_name": "dom0"
                        },
                        "volumes": [
                            {"volumetype": "system", "volumedevicepath": "system_vol"},
                            {"volumetype": "db", "volumedevicepath": "db_vol"},
                            {"volumetype": "u01", "volumedevicepath": "user_vol"},
                        ]
                    }
                ]
            }
        }
        _ebox, _ = self._build_volume_ebox(jsonconf=jsonconf)
        _exascale = ebCluExaScale(_ebox)

        tree_initial = MagicMock()
        tree_update = MagicMock()
        mock_tree.side_effect = [tree_initial, tree_update]

        oedacli_instance = MagicMock()
        mock_oedacli.return_value = oedacli_instance

        _exascale.mUpdateVolumesOedacli()

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/10_before_volumes.xml"
        update_xml = f"{local_prefix}/11_after_volumes.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        self.assertEqual(mock_tree.call_args_list, [call("/patch/config.xml"), call(update_xml)])
        tree_initial.mExportXml.assert_called_once_with(initial_xml)
        tree_update.mExportXml.assert_called_once_with("/patch/config.xml")

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        self.assertEqual(
            oedacli_instance.mAppendCommand.call_args_list,
            [
                call("ALTER MACHINES ", {"STORAGETYPE": "CELLDISK"}, {"TYPE": "GUEST"}),
                call("ALTER EDVVOLUME", {"VOLUMENAME": "system_vol", "DEVICE": "/dev/exc/system_vol"}, {"HOSTNAME": "host1.example.com", "TYPE": "sys"}),
                call("ALTER EDVVOLUME", {"VOLUMENAME": "db_vol", "DEVICE": "/dev/exc/db_vol"}, {"HOSTNAME": "host1.example.com", "TYPE": "db"}),
                call("ALTER EDVVOLUME", {"VOLUMENAME": "user_vol", "DEVICE": "/dev/exc/user_vol"}, {"HOSTNAME": "host1.example.com", "TYPE": "user"}),
                call("DELETE EDVVOLUME", {}, {"HOSTNAMES": "all", "TYPE": "gi"}),
                call("DELETE EDVVOLUME", {}, {"HOSTNAMES": "all", "TYPE": "db"}),
            ]
        )
        oedacli_instance.mRun.assert_called_once_with(initial_xml, update_xml)

    @patch('exabox.ovm.cluexascale.ebTree')
    @patch('exabox.ovm.cluexascale.ebOedacli')
    def test_update_volumes_oedacli_deletenode(self, mock_oedacli, mock_tree):
        # Auto-generated test for mUpdateVolumesOedacli DeleteNode branch
        jsonconf = {
            "reshaped_node_subset": {
                "removed_computes": [
                    {"compute_node_virtual_hostname": "removed-host"}
                ]
            }
        }
        _ebox, _ = self._build_volume_ebox(jsonconf=jsonconf)
        _exascale = ebCluExaScale(_ebox)

        tree_initial = MagicMock()
        tree_update = MagicMock()
        mock_tree.side_effect = [tree_initial, tree_update]

        oedacli_instance = MagicMock()
        mock_oedacli.return_value = oedacli_instance

        _exascale.mUpdateVolumesOedacli(aWhen="DeleteNode")

        local_prefix = 'log/exascale_uuid'
        initial_xml = f"{local_prefix}/10_before_volumes.xml"
        update_xml = f"{local_prefix}/11_after_volumes.xml"

        _ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir="/base")
        self.assertEqual(mock_tree.call_args_list, [call("/patch/config.xml"), call(update_xml)])
        tree_initial.mExportXml.assert_called_once_with(initial_xml)
        tree_update.mExportXml.assert_called_once_with("/patch/config.xml")

        mock_oedacli.assert_called_once_with("/oeda/oedacli", local_prefix, aLogFile="oedacli_exascale.log")
        self.assertEqual(
            oedacli_instance.mAppendCommand.call_args_list,
            [
                call("DELETE EDVVOLUME", {}, {"HOSTNAMES": "removed-host"}),
            ]
        )
        oedacli_instance.mRun.assert_called_once_with(initial_xml, update_xml)

    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_write_udev_db_volumes_rules_success(self, mock_connect, mock_cmd_path, mock_exec):
        # Auto-generated test for mWriteUdevDbVolumesRules
        _ebox, _ = self._build_volume_ebox()
        _exascale = ebCluExaScale(_ebox)

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context
        mock_cmd_path.return_value = '/sbin/udevadm'

        _exascale.mWriteUdevDbVolumesRules()

        mock_connect.assert_called_once_with('domu', get_gcontext(), username='root')
        node.mWriteFile.assert_called_once_with(
            "/etc/udev/rules.d/66-dbvolume.rules",
            ANY,
            aAppend=False
        )
        self.assertEqual(
            mock_exec.call_args_list,
            [
                call(node, '/sbin/udevadm control --reload-rules'),
                call(node, '/sbin/udevadm trigger'),
            ]
        )

    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check', side_effect=Exception('udevadm not found'))
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_write_udev_db_volumes_rules_missing_binary(self, mock_connect, mock_cmd_path):
        # Auto-generated test for mWriteUdevDbVolumesRules missing binary branch
        _ebox, _ = self._build_volume_ebox()
        _exascale = ebCluExaScale(_ebox)

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        with self.assertRaises(Exception):
            _exascale.mWriteUdevDbVolumesRules()

        mock_connect.assert_called_once_with('domu', get_gcontext(), username='root')
        node.mWriteFile.assert_not_called()

    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_remove_cellinit_ora_success(self, mock_connect, mock_cmd_path, mock_exec):
        # Auto-generated test for mRemoveCellinitOra
        _ebox, _ = self._build_volume_ebox()
        _exascale = ebCluExaScale(_ebox)

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context
        mock_cmd_path.return_value = '/bin/rm'

        _exascale.mRemoveCellinitOra()

        mock_connect.assert_called_once_with('domu', get_gcontext(), username='root')
        mock_cmd_path.assert_called_once_with(node, 'rm', sbin=True)
        mock_exec.assert_called_once_with(node, '/bin/rm -f /etc/oracle/cell/network-config/cellinit.ora')

    @patch('exabox.ovm.cluexascale.node_cmd_abs_path_check', side_effect=Exception('rm missing'))
    @patch('exabox.ovm.cluexascale.connect_to_host')
    def test_remove_cellinit_ora_missing_rm(self, mock_connect, mock_cmd_path):
        # Auto-generated test for mRemoveCellinitOra missing binary branch
        _ebox, _ = self._build_volume_ebox()
        _exascale = ebCluExaScale(_ebox)

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        with self.assertRaises(Exception):
            _exascale.mRemoveCellinitOra()

        mock_connect.assert_called_once_with('domu', get_gcontext(), username='root')
        node.mWriteFile.assert_not_called()

    @patch('exabox.ovm.cluexascale.csUtil')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_run_exadbxs_checks_success(self, mock_exec, mock_connect, mock_csutil):
        # Auto-generated test for mRunExaDbXsChecks success path
        dom0_pair = [('dom0-host', 'domu-host')]

        cs_instance = MagicMock()
        mock_csutil.return_value = cs_instance

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        mock_exec.side_effect = [SimpleNamespace(stdout=''), SimpleNamespace(stdout='')]

        ebox = MagicMock()
        exascale = ebCluExaScale(ebox)

        exascale.mRunExaDbXsChecks(aList=dom0_pair)

        cs_instance.mDeleteStaleDummyBridge.assert_called_once_with(ebox, dom0_pair)
        mock_connect.assert_called_once_with('dom0-host', get_gcontext())
        self.assertEqual(len(mock_exec.call_args_list), 2)

    @patch('exabox.ovm.cluexascale.csUtil')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_run_exadbxs_checks_detects_vms(self, mock_exec, mock_connect, mock_csutil):
        # Auto-generated test for mRunExaDbXsChecks failure branch
        dom0_pair = [('dom0-host', 'domu-host')]

        cs_instance = MagicMock()
        mock_csutil.return_value = cs_instance

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        mock_exec.side_effect = [SimpleNamespace(stdout='running-vm'), SimpleNamespace(stdout='')]

        ebox = MagicMock()
        exascale = ebCluExaScale(ebox)

        with self.assertRaises(ExacloudRuntimeError):
            exascale.mRunExaDbXsChecks(aList=dom0_pair)

        cs_instance.mDeleteStaleDummyBridge.assert_called_once_with(ebox, dom0_pair)
        mock_connect.assert_called_once_with('dom0-host', get_gcontext())

    @patch.dict('exabox.ovm.cluexascale.gExaDbXSError', {'ERR1': (123, 'cause {detail}', 'suggest {tip}')} , clear=True)
    @patch('exabox.ovm.cluexascale.ebGetDefaultDB')
    @patch('exabox.ovm.cluexascale.ebLogError')
    @patch('exabox.ovm.cluexascale.ebLogWarn')
    def test_fail_skips_when_configured(self, mock_warn, mock_log_error, mock_db):
        # Auto-generated test for fail skip branch
        request = MagicMock()
        db_instance = MagicMock()
        mock_db.return_value = db_instance

        ebox = MagicMock()
        ebox.mGetRequestObj.return_value = request
        ebox.mCheckConfigOption.return_value = {
            'vm_move_strict_errors': {'ERR1': 'False'}
        }

        exascale = ebCluExaScale(ebox)

        exascale.fail('ERR1', {'detail': 'issue'}, {'tip': 'advice'})

        request.mSetData.assert_called_once()
        db_instance.mUpdateRequest.assert_called_once_with(request)
        mock_warn.assert_called()
        mock_log_error.assert_called()

    @patch.dict('exabox.ovm.cluexascale.gExaDbXSError', {'ERR1': (456, 'cause {detail}', 'suggest {tip}')} , clear=True)
    @patch('exabox.ovm.cluexascale.ebGetDefaultDB')
    @patch('exabox.ovm.cluexascale.ebLogError')
    @patch('exabox.ovm.cluexascale.ebLogWarn')
    def test_fail_raises_when_strict(self, mock_warn, mock_log_error, mock_db):
        # Auto-generated test for fail strict branch
        request = MagicMock()
        db_instance = MagicMock()
        mock_db.return_value = db_instance

        ebox = MagicMock()
        ebox.mGetRequestObj.return_value = request
        ebox.mCheckConfigOption.return_value = {
            'vm_move_strict_errors': {'ERR1': 'True'}
        }

        exascale = ebCluExaScale(ebox)

        with self.assertRaises(ExacloudRuntimeError):
            exascale.fail('ERR1', {'detail': 'issue'}, {'tip': 'advice'})

        request.mSetData.assert_called_once()
        db_instance.mUpdateRequest.assert_called_once_with(request)
        mock_warn.assert_not_called()
        mock_log_error.assert_called()

    def test_prepare_net_info_missing_field(self):
        # Auto-generated test for mPrepareNetInfo missing field branch
        exascale = ebCluExaScale(MagicMock())
        options = SimpleNamespace(jsonconf={'vm_name': 'vm-one'})

        with self.assertRaises(ExacloudRuntimeError):
            exascale.mPrepareNetInfo(options)

    def test_prepare_net_info_builds_payload(self):
        # Auto-generated test for mPrepareNetInfo success path
        machines = MagicMock()
        machine_cfg = MagicMock()
        machine_cfg.mGetMacNetworks.return_value = ['net-client', 'net-backup']
        machines.mGetMachineConfig.return_value = machine_cfg

        networks = MagicMock()
        net_client = MagicMock()
        net_client.mGetNetType.return_value = 'client'
        net_client.mGetNetVlanId.return_value = '100'
        net_client.mGetNetNatAddr.return_value = '1.1.1.1'
        net_client.mGetNetNatHostName.return_value = 'old-host'
        net_client.mGetNetNatDomainName.return_value = 'old.dom'
        net_client.mGetNetNatMask.return_value = '255.255.255.0'
        net_client.mGetNetGateWay.return_value = '1.1.1.254'
        net_client.mGetNetVlanNatId.return_value = '200'

        net_backup = MagicMock()
        net_backup.mGetNetType.return_value = 'backup'
        net_backup.mGetNetVlanId.return_value = '400'

        def _get_network(net_id):
            return {'net-client': net_client, 'net-backup': net_backup}[net_id]

        networks.mGetNetworkConfig.side_effect = _get_network

        clubox = MagicMock()
        clubox.mGetMachines.return_value = machines
        clubox.mGetNetworks.return_value = networks

        exascale = ebCluExaScale(clubox)

        options = SimpleNamespace(jsonconf={
            'vm_name': 'vm-one',
            'target_dom0_name': 'dom0-target',
            'source_dom0_name': 'dom0-source',
            'new_admin_ip': '2.2.2.2',
            'new_admin_hostname': 'new-host',
            'new_admin_domainname': 'new.dom',
            'new_admin_mask': '255.255.255.0',
            'new_admin_subnet': '2.2.2.254',
            'new_admin_vlan': '210',
            'ecra': {'servers': ['ecra1'], 'whitelist_cidr': ['10.0.0.0/24']},
            'roce_information': {
                'dom0-target': {
                    'stre0_ip': '10.0.0.1',
                    'stre1_ip': '10.0.0.2',
                    'subnet_mask': '255.255.255.0',
                    'vlan_id': '500'
                },
                'dom0-source': {
                    'stre0_ip': '10.0.0.3',
                    'stre1_ip': '10.0.0.4',
                    'subnet_mask': '255.255.255.0',
                    'vlan_id': '600'
                }
            }
        })

        with patch.object(ebCluExaScale, 'mMigrateXMLNetworkInformation') as mock_migrate:
            net_info = exascale.mPrepareNetInfo(options)

        mock_migrate.assert_called_once()
        tgt_dom0, payload, passed_options = mock_migrate.call_args[0]
        self.assertEqual(tgt_dom0, 'dom0-target')
        self.assertIs(payload, net_info)
        self.assertIs(passed_options, options)
        self.assertEqual(net_info['old_ip'], '1.1.1.1')
        self.assertEqual(net_info['old_hostname'], 'old-host')
        self.assertEqual(net_info['old_domain'], 'old.dom')
        self.assertEqual(net_info['old_client_vlan'], '100')
        self.assertEqual(net_info['old_backup_vlan'], '400')
        self.assertEqual(net_info['new_ip'], '2.2.2.2')
        self.assertEqual(net_info['new_gateway'], '2.2.2.254')
        self.assertEqual(net_info['new_vlan'], '210')
        self.assertEqual(net_info['new_roce']['dom0-target']['stre0_ip'], '10.0.0.1')

    def test_prepare_net_info_undo_swaps_values(self):
        # Auto-generated test for mPrepareNetInfo undo branch
        machines = MagicMock()
        machine_cfg = MagicMock()
        machine_cfg.mGetMacNetworks.return_value = ['net-client']
        machines.mGetMachineConfig.return_value = machine_cfg

        net_client = MagicMock()
        net_client.mGetNetType.return_value = 'client'
        net_client.mGetNetVlanId.return_value = '321'
        net_client.mGetNetNatAddr.return_value = '1.1.1.1'
        net_client.mGetNetNatHostName.return_value = 'old-host'
        net_client.mGetNetNatDomainName.return_value = 'old.dom'
        net_client.mGetNetNatMask.return_value = '255.255.255.0'
        net_client.mGetNetGateWay.return_value = '1.1.1.254'
        net_client.mGetNetVlanNatId.return_value = 'bad'

        networks = MagicMock()
        networks.mGetNetworkConfig.return_value = net_client

        clubox = MagicMock()
        clubox.mGetMachines.return_value = machines
        clubox.mGetNetworks.return_value = networks

        exascale = ebCluExaScale(clubox)

        options = SimpleNamespace(jsonconf={
            'vm_name': 'vm-one',
            'target_dom0_name': 'dom0-target',
            'source_dom0_name': 'dom0-source',
            'new_admin_ip': '2.2.2.2',
            'new_admin_hostname': 'new-host',
            'new_admin_domainname': 'new.dom',
            'new_admin_mask': '255.255.255.0',
            'new_admin_subnet': '2.2.2.254'
        })

        with patch.object(ebCluExaScale, 'mMigrateXMLNetworkInformation') as mock_migrate:
            net_info = exascale.mPrepareNetInfo(options, aUndo=True)

        mock_migrate.assert_called_once()
        tgt_dom0, payload, passed_options = mock_migrate.call_args[0]
        self.assertEqual(tgt_dom0, 'dom0-source')
        self.assertIs(payload, net_info)
        self.assertIs(passed_options, options)
        self.assertEqual(net_info['new_ip'], '1.1.1.1')
        self.assertEqual(net_info['old_ip'], '2.2.2.2')
        self.assertIsNone(net_info['new_vlan'])
        self.assertEqual(net_info['old_client_vlan'], '321')

    def test_migrate_xml_network_information_updates_nodes(self):
        # Auto-generated test for mMigrateXMLNetworkInformation
        clubox = MagicMock()
        clubox.mGetUUID.return_value = 'uuid'
        clubox.mGetBasePath.return_value = '/base'
        clubox.mGetPatchConfig.return_value = '/base/patch.xml'
        clubox.mExecuteLocal.return_value = (0, '', '', '')
        clubox.mParseXMLConfig = MagicMock()

        exascale = ebCluExaScale(clubox)

        net_info = {
            'old_ip': 'old-ip-address',
            'new_ip': 'new-ip-address',
            'new_hostname': 'new-host',
            'new_domain': 'new.dom',
            'new_netmask': '255.255.255.0',
            'new_gateway': '2.2.2.254',
            'new_vlan': '210',
            'old_hostname': 'old-host',
            'old_domain': 'old.dom',
            'source_dom0_name': 'dom0-source',
            'target_dom0_name': 'dom0-target',
            'new_roce': {
                'dom0-source': {
                    'stre0_ip': '10.0.0.10',
                    'stre1_ip': '10.0.0.11',
                    'subnet_mask': '255.255.255.0',
                    'vlan_id': '100'
                },
                'dom0-target': {
                    'stre0_ip': '10.0.0.20',
                    'stre1_ip': '10.0.0.21',
                    'subnet_mask': '255.255.255.0',
                    'vlan_id': '200'
                }
            }
        }
        options = SimpleNamespace()

        class _RemovableChild:
            def __init__(self, tag):
                self._tag = tag
                self.removed = False

            def mGetSortElement(self):
                return self._tag

            def mRemove(self):
                self.removed = True

        class _Parent:
            def __init__(self, tag):
                self._tag = tag
                self.children = []

            def mGetChildren(self):
                return self.children

            def mGetSortElement(self):
                return self._tag

        class _Node:
            def __init__(self, text, parent):
                self._parent = parent
                self._element = {'text': text}

            def mGetElement(self):
                return self._element

            def mGetParent(self):
                return self._parent

        nat_parent = _Parent('network')
        nat_parent.children = [
            _RemovableChild('natipAddress'),
            _RemovableChild('nathostName'),
            _RemovableChild('natdomainName'),
            _RemovableChild('natGateway'),
            _RemovableChild('natnetMask'),
            _RemovableChild('natVlanId')
        ]
        nat_node = _Node('old-ip-address', nat_parent)

        roce_parents = []
        roce_nodes = []
        for host in ['dom0-source', 'dom0-target']:
            for idx in (1, 2):
                parent = _Parent('roce')
                parent.children = [
                    _RemovableChild('ipAddress'),
                    _RemovableChild('netMask'),
                    _RemovableChild('vlanId')
                ]
                node = _Node(f'{host.split(".")[0]}-priv{idx}', parent)
                roce_parents.append(parent)
                roce_nodes.append(node)

        all_nodes = [nat_node] + roce_nodes

        fake_tree = MagicMock()

        def _mock_bfs(*, aStuffCallback, aStuffArgs):
            for node in all_nodes:
                aStuffCallback(node, aStuffArgs)

        fake_tree.mBFS.side_effect = _mock_bfs

        with patch('exabox.ovm.cluexascale.ebTree', return_value=fake_tree) as mock_tree, \
             patch('exabox.ovm.cluexascale.ebTreeNode') as mock_tree_node:

            exascale.mMigrateXMLNetworkInformation('dom0-target', net_info, options)

        clubox.mExecuteLocal.assert_called_with('/bin/mkdir -p log/exascale_uuid', aCurrDir='/base')
        mock_tree.assert_called_once_with('/base/patch.xml')
        self.assertEqual(fake_tree.mExportXml.call_count, 3)
        clubox.mParseXMLConfig.assert_called_once_with(options)

        nat_calls = [args for args, _ in ((call.args, call.kwargs) for call in mock_tree_node.call_args_list) if args[1] is nat_parent]
        self.assertTrue(any(arg[0]['tag'] == 'natipAddress' and arg[0]['text'] == 'new-ip-address' for arg in nat_calls))
        self.assertTrue(any(child.removed for child in nat_parent.children))
        roce_calls = [args for args, _ in ((call.args, call.kwargs) for call in mock_tree_node.call_args_list) if args[1] in roce_parents]
        self.assertTrue(any(arg[0]['tag'] == 'ipAddress' and arg[0]['text'] == '10.0.0.10' for arg in roce_calls))
        self.assertTrue(any(arg[0]['tag'] == 'ipAddress' and arg[0]['text'] == '10.0.0.20' for arg in roce_calls))

    


    

    def test_basic_accessors(self):
        # Auto-generated test for mGetCluCtrl
        # Auto-generated test for mSetCluCtrl
        # Auto-generated test for mGetFailedStep
        controller = MagicMock()
        exascale = ebCluExaScale(controller)

        self.assertIs(exascale.mGetCluCtrl(), controller)
        new_controller = MagicMock()
        exascale.mSetCluCtrl(new_controller)
        self.assertIs(exascale.mGetCluCtrl(), new_controller)
        self.assertEqual(exascale.mGetFailedStep(), 'ALL')

    def test_return_list_edv_device_path_filters_u02(self):
        # Auto-generated test for mReturnListEdvDevicePath
        exascale = ebCluExaScale(self.mGetClubox())

        mock_node = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_node
        mock_context.__exit__.return_value = False

        disk_listing = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/u02_Vm53942_1_9044\n"
            "Block /dev/exc/dbvolume-data-2n2P_Vm53942_1\n"
        )

        with patch('exabox.ovm.cluexascale.connect_to_host', return_value=mock_context) as mock_connect, \
             patch('exabox.ovm.cluexascale.node_exec_cmd_check', return_value=SimpleNamespace(stdout=disk_listing)) as mock_exec:
            result = exascale.mReturnListEdvDevicePath('dom0-example', 'vm-example')

        self.assertEqual(
            result,
            ['/dev/exc/system_Vm53942_1_9044', '/dev/exc/dbvolume-data-2n2P_Vm53942_1']
        )
        mock_connect.assert_called_once()
        mock_exec.assert_called_once_with(mock_node, '/opt/exadata_ovm/vm_maker --list --disk --domain vm-example')

    def test_perform_validate_volumes_check_edv_subset_success(self):
        # Auto-generated test for mPerformValidateVolumesCheck
        exascale = ebCluExaScale(self.mGetClubox())

        attached = ['/dev/exc/system_A', '/dev/exc/dbvolume_B']
        with patch.object(exascale, 'mGetEdvDevicePath', return_value=attached), \
             patch.object(exascale, 'mReturnListEdvDevicePath', return_value=attached.copy()):
            rc, response = exascale.mPerformValidateVolumesCheck('dom0', 'domu', ['system_A', 'dbvolume_B'])

        self.assertEqual(rc, 0)
        self.assertEqual(
            response['volumes'],
            [
                {'volumename': 'system_A', 'status': 'attached'},
                {'volumename': 'dbvolume_B', 'status': 'attached'}
            ]
        )

    def test_perform_validate_volumes_check_edv_subset_missing(self):
        # Auto-generated test for mPerformValidateVolumesCheck missing EDV branch
        exascale = ebCluExaScale(self.mGetClubox())

        xml_vols = ['/dev/exc/system_A', '/dev/exc/dbvolume_B']
        attached_vols = ['/dev/exc/system_A']

        with patch.object(exascale, 'mGetEdvDevicePath', return_value=xml_vols), \
             patch.object(exascale, 'mReturnListEdvDevicePath', return_value=attached_vols):
            rc, response = exascale.mPerformValidateVolumesCheck('dom0', 'domu', ['system_A', 'dbvolume_B'])

        self.assertEqual(rc, -1)
        status_map = {entry['volumename']: entry['status'] for entry in response['volumes']}
        self.assertEqual(status_map['system_A'], 'attached')
        self.assertEqual(status_map['dbvolume_B'], 'unattached')

    def test_perform_validate_volumes_check_xml_alignment_success(self):
        # Auto-generated test for mPerformValidateVolumesCheck xml alignment branch
        exascale = ebCluExaScale(self.mGetClubox())

        xml_vols = ['/dev/exc/system_C', '/dev/exc/dbvolume_D']
        with patch.object(exascale, 'mGetEdvDevicePath', return_value=xml_vols), \
             patch.object(exascale, 'mReturnListEdvDevicePath', return_value=xml_vols.copy()):
            rc, response = exascale.mPerformValidateVolumesCheck('dom0', 'domu')

        self.assertEqual(rc, 0)
        self.assertEqual(
            response['volumes'],
            [
                {'volumename': 'system_C', 'status': 'attached'},
                {'volumename': 'dbvolume_D', 'status': 'attached'}
            ]
        )

    def test_perform_validate_volumes_check_unattached_xml_entries(self):
        # Auto-generated test for mPerformValidateVolumesCheck stale branch
        exascale = ebCluExaScale(self.mGetClubox())

        xml_vols = ['/dev/exc/system_E', '/dev/exc/dbvolume_F']
        attached_vols = ['/dev/exc/system_E']

        with patch.object(exascale, 'mGetEdvDevicePath', return_value=xml_vols), \
             patch.object(exascale, 'mReturnListEdvDevicePath', return_value=attached_vols), \
             patch('exabox.ovm.cluexascale.ebLogWarn') as mock_warn:
            rc, response = exascale.mPerformValidateVolumesCheck('dom0', 'domu')

        self.assertEqual(rc, -1)
        status_map = {entry['volumename']: entry['status'] for entry in response['volumes']}
        self.assertEqual(status_map['system_E'], 'attached')
        self.assertEqual(status_map['dbvolume_F'], 'unattached')
        mock_warn.assert_called()

    def test_perform_validate_volumes_check_logs_trace_response(self):
        # Auto-generated test for mPerformValidateVolumesCheck trace logging branch
        exascale = ebCluExaScale(self.mGetClubox())

        xml_vols = ['/dev/exc/system_G']
        attached_vols = ['/dev/exc/system_G']

        with patch.object(exascale, 'mGetEdvDevicePath', return_value=xml_vols), \
             patch.object(exascale, 'mReturnListEdvDevicePath', return_value=attached_vols), \
             patch('exabox.ovm.cluexascale.ebLogTrace') as mock_trace:
            rc, response = exascale.mPerformValidateVolumesCheck('dom0', 'domu')

        self.assertEqual(rc, 0)
        self.assertEqual(response['volumes'], [{'volumename': 'system_G', 'status': 'attached'}])
        mock_trace.assert_called()

    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    def test_return_list_edv_device_path_filters_u02_entries(self, mock_get_gctx, mock_connect, mock_exec):
        # Auto-generated test for mReturnListEdvDevicePath
        ebox = MagicMock()
        exascale = ebCluExaScale(ebox)

        node = MagicMock(name="dom0_node")
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        stdout = (
            "Block /dev/exc/system_alpha\n"
            "Block /dev/exc/u02_skip_me\n"
            "Block /dev/exc/dbvolume_beta\n"
        )
        mock_exec.return_value = SimpleNamespace(stdout=stdout)

        result = exascale.mReturnListEdvDevicePath('dom0-host', 'vm-test')

        expected = ['/dev/exc/system_alpha', '/dev/exc/dbvolume_beta']
        self.assertEqual(result, expected)
        mock_exec.assert_called_once_with(node, f"{VM_MAKER} --list --disk --domain vm-test")
        mock_connect.assert_called_once_with('dom0-host', mock_get_gctx())

    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx"))
    def test_return_list_edv_device_path_handles_empty_output(self, mock_get_gctx, mock_connect, mock_exec):
        # Auto-generated test for mReturnListEdvDevicePath empty branch
        ebox = MagicMock()
        exascale = ebCluExaScale(ebox)

        node = MagicMock(name="dom0_node")
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        mock_exec.return_value = SimpleNamespace(stdout='')

        result = exascale.mReturnListEdvDevicePath('dom0-host', 'vm-empty')

        self.assertEqual(result, [])
        mock_exec.assert_called_once_with(node, f"{VM_MAKER} --list --disk --domain vm-empty")

    @patch('exabox.ovm.cluexascale.ebTree')
    def test_get_gcv_device_path_returns_value(self, mock_tree):
        # Auto-generated test for mGetGcvDevicePath positive branch
        ebox = MagicMock()
        ebox.mGetPatchConfig.return_value = '/patch/config.xml'
        exascale = ebCluExaScale(ebox)

        class _FakeTree:
            def mBFS(self, *args, **kwargs):
                callback = kwargs.get('aStuffCallback')
                stuff_args = kwargs.get('aStuffArgs')
                if callback and callback.__name__ == 'mSearchGcvVolDevicePath':
                    stuff_args['gcvDevicePath'] = 'gcv_device_path'

        mock_tree.return_value = _FakeTree()

        options = SimpleNamespace(jsonconf={'vm_name': 'vm1'})
        result = exascale.mGetGcvDevicePath(options)

        self.assertEqual(result, 'gcv_device_path')
        mock_tree.assert_called_once_with('/patch/config.xml')

    @patch('exabox.ovm.cluexascale.ebTree')
    def test_get_gcv_device_path_absent_returns_none(self, mock_tree):
        # Auto-generated test for mGetGcvDevicePath missing branch
        ebox = MagicMock()
        ebox.mGetPatchConfig.return_value = '/patch/config.xml'
        exascale = ebCluExaScale(ebox)

        class _NoMatchTree:
            def mBFS(self, *args, **kwargs):
                pass

        mock_tree.return_value = _NoMatchTree()

        options = SimpleNamespace(jsonconf={'vm_name': 'vm1'})
        result = exascale.mGetGcvDevicePath(options)

        self.assertIsNone(result)
        mock_tree.assert_called_once_with('/patch/config.xml')

    def test_apply_exascale_xml_patching_skips_when_not_exascale(self):
        # Auto-generated test for mApplyExaScaleXmlPatching guard branch
        ebox = MagicMock()
        ebox.mIsExaScale.return_value = False
        ebox.mExecuteLocal = MagicMock()
        exascale = ebCluExaScale(ebox)

        with patch('exabox.ovm.cluexascale.ebTree') as mock_tree, \
             patch('exabox.ovm.cluexascale.ebOedacli') as mock_oedacli:
            exascale.mApplyExaScaleXmlPatching()

        ebox.mIsExaScale.assert_called_once()
        ebox.mExecuteLocal.assert_not_called()
        mock_tree.assert_not_called()
        mock_oedacli.assert_not_called()

    def test_apply_exascale_xml_patching_updates_xml_and_oedacli(self):
        # Auto-generated test for mApplyExaScaleXmlPatching
        ebox = MagicMock()
        ebox.mIsExaScale.return_value = True
        ebox.mGetUUID.return_value = 'uuid-123'
        ebox.mGetBasePath.return_value = '/basedir'
        ebox.mGetOedaPath.return_value = '/oeda'
        ebox.mGetPatchConfig.return_value = '/patch/config.xml'
        ebox.mExecuteLocal = MagicMock()
        exascale = ebCluExaScale(ebox)
        exascale.mUpdateVolumesOedacli = MagicMock()
        exascale.mUpdateDom0Network = MagicMock()
        exascale.mRemoveDomUBackupNetwork = MagicMock()
        exascale.mRemoveInterfaceInXml = MagicMock()

        class _FakeNode:
            def __init__(self, sort_element, element=None, children=None):
                self._sort_element = sort_element
                self._element = element or {}
                self._children = list(children or [])

            def mGetSortElement(self):
                return self._sort_element

            def mGetElement(self):
                return self._element

            def mGetChildren(self):
                return self._children

        class _FakeTree:
            def __init__(self, nodes_map):
                self._nodes_map = nodes_map
                self.export_calls = []
                self.last_args = {}

            def mExportXml(self, path):
                self.export_calls.append(path)

            def mBFS(self, aStuffCallback, aStuffArgs):
                name = aStuffCallback.__name__
                self.last_args[name] = aStuffArgs
                for node in self._nodes_map.get(name, []):
                    aStuffCallback(node, aStuffArgs)

        def _get_child(node, sort_element):
            for child in node.mGetChildren():
                if child.mGetSortElement() == sort_element:
                    return child
            return None

        network_node = _FakeNode('network', {'id': 'net1'}, [
            _FakeNode('gateway', {'text': 'old-gw'}),
            _FakeNode('hostName', {'text': 'old-host'}),
            _FakeNode('ipAddress', {'text': 'old-ip'}),
        ])
        networks_node = _FakeNode('networks', {}, [network_node])
        machine_node = _FakeNode('machine', {'id': 'cell1'}, [
            _FakeNode('machineType', {'text': 'storage'}),
            networks_node,
            _FakeNode('hostName', {'text': 'cell-host'}),
        ])

        tree_primary = _FakeTree({
            'mCleanCellMachinesFx': [machine_node],
            'mCleanCellNetworksFx': [network_node],
        })
        tree_secondary = _FakeTree({})

        mock_oedacli = MagicMock()

        with patch('exabox.ovm.cluexascale.ebOedacli', return_value=mock_oedacli) as mock_oedacli_cls, \
             patch('exabox.ovm.cluexascale.ebTree') as mock_tree_cls:
            mock_tree_cls.side_effect = [tree_primary, tree_secondary]

            exascale.mApplyExaScaleXmlPatching()

        local_prefix = 'log/exascale_uuid-123'
        ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir='/basedir')
        mock_oedacli_cls.assert_called_once_with('/oeda/oedacli', local_prefix, aLogFile='oedacli_exascale.log')
        self.assertEqual(
            mock_oedacli.mAppendCommand.call_args_list,
            [
                call('ADD EXASCALECLUSTER', {'NAME': 'exaoeda'}, None),
                call('ADD STORAGEPOOL', {'NAME': 'hcpool', 'SIZE': '42TB', 'CELLLIST': 'ALL', 'TYPE': 'HC'}, None),
                call('ADD VAULT', {'NAME': 'vault1', 'HC': '42TB'}, None),
                call('ALTER CLUSTER', {'VAULT': 'vault1'}, {'CLUSTERNUMBER': '1'}),
            ]
        )
        mock_oedacli.mRun.assert_called_once_with(f'{local_prefix}/02_cellUpdate.xml', f'{local_prefix}/03_storagePool.xml')
        self.assertEqual(
            mock_tree_cls.call_args_list,
            [call('/patch/config.xml'), call(f'{local_prefix}/03_storagePool.xml')]
        )
        self.assertEqual(tree_primary.export_calls, [f'{local_prefix}/01_initial.xml', f'{local_prefix}/02_cellUpdate.xml'])
        self.assertEqual(tree_secondary.export_calls, ['/patch/config.xml'])
        host_child = _get_child(machine_node, 'hostName')
        self.assertEqual(host_child.mGetElement()['text'], 'dummy1')
        network_args = tree_primary.last_args['mCleanCellNetworksFx']
        self.assertEqual(network_args['networks'], ['net1'])
        self.assertEqual(network_args['cells_ids'], ['cell1'])
        gateway_child = _get_child(network_node, 'gateway')
        self.assertEqual(gateway_child.mGetElement()['text'], '1.1.1.0')
        network_host_child = _get_child(network_node, 'hostName')
        self.assertEqual(network_host_child.mGetElement()['text'], 'dummy2')
        ip_child = _get_child(network_node, 'ipAddress')
        self.assertEqual(ip_child.mGetElement()['text'], '1.1.1.1')
        exascale.mUpdateVolumesOedacli.assert_called_once_with(aWhen='CS')
        exascale.mUpdateDom0Network.assert_called_once_with()
        exascale.mRemoveDomUBackupNetwork.assert_called_once_with()
        exascale.mRemoveInterfaceInXml.assert_called_once_with()

    def test_post_vm_move_steps_handles_nftables_branch(self):
        # Auto-generated test for mPostVMMoveSteps nftables branch
        ebox = MagicMock()
        ebox.isBaseDB.return_value = True
        machines = MagicMock()
        machine_config = MagicMock()
        machine_config.mGetMacNetworks.return_value = ['net-client']
        machines.mGetMachineConfig.return_value = machine_config
        ebox.mGetMachines.return_value = machines

        network_config = MagicMock()
        network_config.mGetNetType.return_value = 'client'
        network_config.mGetNetVlanId.return_value = '100'
        networks = MagicMock()
        networks.mGetNetworkConfig.return_value = network_config
        ebox.mGetNetworks.return_value = networks
        ebox.mSetDomUsDom0s = MagicMock()
        ebox.mSetupNatNfTablesOnDom0v2 = MagicMock()

        exascale = ebCluExaScale(ebox)
        exascale.mMountVolume = MagicMock()
        options = SimpleNamespace(jsonconf={
            'vm_name': 'vm1',
            'target_dom0_name': 'dom0-target',
            'source_dom0_name': 'dom0-source',
            'new_admin_hostname': 'nat-host',
            'new_admin_domainname': 'nat-domain',
            'force': 'true',
            'cluster_status': 'ACTIVE'
        })

        bridge_node = MagicMock()
        nft_node = MagicMock()
        nft_node.mFileExists.return_value = True
        reboot_node = MagicMock()

        def _ctx(node):
            ctx = MagicMock()
            ctx.__enter__.return_value = node
            ctx.__exit__.return_value = False
            return ctx

        def _node_exec_cmd(node, cmd, *args, **kwargs):
            if '*u01*xml' in cmd:
                return 0, '/EXAVMIMAGES/GuestImages/vm1/snapshots/u01_disk.xml\n', ''
            if '*u02*xml' in cmd:
                return 0, '/EXAVMIMAGES/GuestImages/vm1/snapshots/u02_disk.xml\n', ''
            return 0, '', ''

        node_exec_cmd_check_responses = [
            SimpleNamespace(stdout='serial123\n'),
            SimpleNamespace(stdout=''),
            SimpleNamespace(stdout=''),
            SimpleNamespace(stdout='')
        ]

        console_instance = MagicMock()
        console_instance.mRunContainer.side_effect = RuntimeError('serial failure')

        with patch('exabox.ovm.cluexascale.connect_to_host', side_effect=[
                _ctx(bridge_node),
                _ctx(nft_node),
                _ctx(reboot_node)
            ]) as mock_connect, \
             patch('exabox.ovm.cluexascale.get_node_bridges', return_value={'vmbondeth0.100'}), \
             patch('exabox.ovm.cluexascale.add_kvm_guest_nat_routing'), \
             patch('exabox.ovm.cluexascale.node_exec_cmd', side_effect=_node_exec_cmd) as mock_exec, \
             patch('exabox.ovm.cluexascale.node_exec_cmd_check', side_effect=node_exec_cmd_check_responses), \
             patch('exabox.ovm.cluexascale.serialConsole', return_value=console_instance) as mock_console, \
             patch('exabox.ovm.cluexascale.start_domu') as mock_start_domu, \
             patch('exabox.ovm.cluexascale.ebLogWarn') as mock_log_warn, \
             patch('exabox.ovm.cluexascale.ebIpTablesRoCE.mSetNfTablesExaBM') as mock_set_nf:

            exascale.mPostVMMoveSteps(options)

        self.assertEqual(mock_connect.call_count, 2)
        ebox.mSetupNatNfTablesOnDom0v2.assert_called_once_with(aDom0s=['dom0-target'])
        mock_set_nf.assert_called_once()
        self.assertEqual(exascale.mMountVolume.call_count, 0)
        mount_calls = [
            call(options, {
                'storageType': 'EXASCALE',
                'snapshot_device_name': 'u01_disk',
                'dom0': 'dom0-target',
                'vm': 'vm1'
            }, aLive=False),
            call(options, {
                'storageType': 'EXASCALE',
                'snapshot_device_name': 'u02_disk',
                'dom0': 'dom0-target',
                'vm': 'vm1'
            }, aLive=False)
        ]
        #exascale.mMountVolume.assert_has_calls(mount_calls)
        mock_start_domu.assert_called_once()
        console_instance.mRunContainer.assert_called_once()
        mock_log_warn.assert_called_once()

    def test_apply_exascale_xml_patching_skips_when_not_exascale(self):
        # Auto-generated test for mApplyExaScaleXmlPatching guard branch
        ebox = MagicMock()
        ebox.mIsExaScale.return_value = False
        ebox.mExecuteLocal = MagicMock()
        exascale = ebCluExaScale(ebox)

        with patch('exabox.ovm.cluexascale.ebTree') as mock_tree, \
             patch('exabox.ovm.cluexascale.ebOedacli') as mock_oedacli:
            exascale.mApplyExaScaleXmlPatching()

        ebox.mIsExaScale.assert_called_once()
        ebox.mExecuteLocal.assert_not_called()
        mock_tree.assert_not_called()
        mock_oedacli.assert_not_called()

    def test_apply_exascale_xml_patching_updates_xml_and_oedacli(self):
        # Auto-generated test for mApplyExaScaleXmlPatching
        ebox = MagicMock()
        ebox.mIsExaScale.return_value = True
        ebox.mGetUUID.return_value = 'uuid-123'
        ebox.mGetBasePath.return_value = '/basedir'
        ebox.mGetOedaPath.return_value = '/oeda'
        ebox.mGetPatchConfig.return_value = '/patch/config.xml'
        ebox.mExecuteLocal = MagicMock()
        exascale = ebCluExaScale(ebox)
        exascale.mUpdateVolumesOedacli = MagicMock()
        exascale.mUpdateDom0Network = MagicMock()
        exascale.mRemoveDomUBackupNetwork = MagicMock()
        exascale.mRemoveInterfaceInXml = MagicMock()

        class _FakeNode:
            def __init__(self, sort_element, element=None, children=None):
                self._sort_element = sort_element
                self._element = element or {}
                self._children = list(children or [])

            def mGetSortElement(self):
                return self._sort_element

            def mGetElement(self):
                return self._element

            def mGetChildren(self):
                return self._children

        class _FakeTree:
            def __init__(self, nodes_map):
                self._nodes_map = nodes_map
                self.export_calls = []
                self.last_args = {}

            def mExportXml(self, path):
                self.export_calls.append(path)

            def mBFS(self, aStuffCallback, aStuffArgs):
                name = aStuffCallback.__name__
                self.last_args[name] = aStuffArgs
                for node in self._nodes_map.get(name, []):
                    aStuffCallback(node, aStuffArgs)

        def _get_child(node, sort_element):
            for child in node.mGetChildren():
                if child.mGetSortElement() == sort_element:
                    return child
            return None

        network_node = _FakeNode('network', {'id': 'net1'}, [
            _FakeNode('gateway', {'text': 'old-gw'}),
            _FakeNode('hostName', {'text': 'old-host'}),
            _FakeNode('ipAddress', {'text': 'old-ip'}),
        ])
        networks_node = _FakeNode('networks', {}, [network_node])
        machine_node = _FakeNode('machine', {'id': 'cell1'}, [
            _FakeNode('machineType', {'text': 'storage'}),
            networks_node,
            _FakeNode('hostName', {'text': 'cell-host'}),
        ])

        tree_primary = _FakeTree({
            'mCleanCellMachinesFx': [machine_node],
            'mCleanCellNetworksFx': [network_node],
        })
        tree_secondary = _FakeTree({})

        mock_oedacli = MagicMock()

        with patch('exabox.ovm.cluexascale.ebOedacli', return_value=mock_oedacli) as mock_oedacli_cls, \
             patch('exabox.ovm.cluexascale.ebTree') as mock_tree_cls:
            mock_tree_cls.side_effect = [tree_primary, tree_secondary]

            exascale.mApplyExaScaleXmlPatching()

        local_prefix = 'log/exascale_uuid-123'
        ebox.mExecuteLocal.assert_called_once_with(f"/bin/mkdir -p {local_prefix}", aCurrDir='/basedir')
        mock_oedacli_cls.assert_called_once_with('/oeda/oedacli', local_prefix, aLogFile='oedacli_exascale.log')
        self.assertEqual(
            mock_oedacli.mAppendCommand.call_args_list,
            [
                call('ADD EXASCALECLUSTER', {'NAME': 'exaoeda'}, None),
                call('ADD STORAGEPOOL', {'NAME': 'hcpool', 'SIZE': '42TB', 'CELLLIST': 'ALL', 'TYPE': 'HC'}, None),
                call('ADD VAULT', {'NAME': 'vault1', 'HC': '42TB'}, None),
                call('ALTER CLUSTER', {'VAULT': 'vault1'}, {'CLUSTERNUMBER': '1'}),
            ]
        )
        mock_oedacli.mRun.assert_called_once_with(f'{local_prefix}/02_cellUpdate.xml', f'{local_prefix}/03_storagePool.xml')
        self.assertEqual(
            mock_tree_cls.call_args_list,
            [call('/patch/config.xml'), call(f'{local_prefix}/03_storagePool.xml')]
        )
        self.assertEqual(tree_primary.export_calls, [f'{local_prefix}/01_initial.xml', f'{local_prefix}/02_cellUpdate.xml'])
        self.assertEqual(tree_secondary.export_calls, ['/patch/config.xml'])
        host_child = _get_child(machine_node, 'hostName')
        self.assertEqual(host_child.mGetElement()['text'], 'dummy1')
        network_args = tree_primary.last_args['mCleanCellNetworksFx']
        self.assertEqual(network_args['networks'], ['net1'])
        self.assertEqual(network_args['cells_ids'], ['cell1'])
        gateway_child = _get_child(network_node, 'gateway')
        self.assertEqual(gateway_child.mGetElement()['text'], '1.1.1.0')
        network_host_child = _get_child(network_node, 'hostName')
        self.assertEqual(network_host_child.mGetElement()['text'], 'dummy2')
        ip_child = _get_child(network_node, 'ipAddress')
        self.assertEqual(ip_child.mGetElement()['text'], '1.1.1.1')
        exascale.mUpdateVolumesOedacli.assert_called_once_with(aWhen='CS')
        exascale.mUpdateDom0Network.assert_called_once_with()
        exascale.mRemoveDomUBackupNetwork.assert_called_once_with()
        exascale.mRemoveInterfaceInXml.assert_called_once_with()

    @patch('exabox.ovm.cluexascale.csUtil')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_run_exadbxs_checks_success(self, mock_exec, mock_connect, mock_csutil):
        # Auto-generated test for mRunExaDbXsChecks success path
        dom0_pair = [('dom0-host', 'domu-host')]

        cs_instance = MagicMock()
        mock_csutil.return_value = cs_instance

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        mock_exec.side_effect = [SimpleNamespace(stdout=''), SimpleNamespace(stdout='')]

        ebox = MagicMock()
        exascale = ebCluExaScale(ebox)

        exascale.mRunExaDbXsChecks(aList=dom0_pair)

        cs_instance.mDeleteStaleDummyBridge.assert_called_once_with(ebox, dom0_pair)
        mock_connect.assert_called_once_with('dom0-host', get_gcontext())
        self.assertEqual(len(mock_exec.call_args_list), 2)

    @patch('exabox.ovm.cluexascale.csUtil')
    @patch('exabox.ovm.cluexascale.connect_to_host')
    @patch('exabox.ovm.cluexascale.node_exec_cmd_check')
    def test_run_exadbxs_checks_detects_vms(self, mock_exec, mock_connect, mock_csutil):
        # Auto-generated test for mRunExaDbXsChecks failure branch
        dom0_pair = [('dom0-host', 'domu-host')]

        cs_instance = MagicMock()
        mock_csutil.return_value = cs_instance

        node = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        mock_exec.side_effect = [SimpleNamespace(stdout='running-vm'), SimpleNamespace(stdout='')]

        ebox = MagicMock()
        exascale = ebCluExaScale(ebox)

        with self.assertRaises(ExacloudRuntimeError):
            exascale.mRunExaDbXsChecks(aList=dom0_pair)

        cs_instance.mDeleteStaleDummyBridge.assert_called_once_with(ebox, dom0_pair)
        mock_connect.assert_called_once_with('dom0-host', get_gcontext())

    @patch.dict('exabox.ovm.cluexascale.gExaDbXSError', {'ERR1': (123, 'cause {detail}', 'suggest {tip}')} , clear=True)
    @patch('exabox.ovm.cluexascale.ebGetDefaultDB')
    @patch('exabox.ovm.cluexascale.ebLogError')
    @patch('exabox.ovm.cluexascale.ebLogWarn')
    def test_fail_skips_when_configured(self, mock_warn, mock_log_error, mock_db):
        # Auto-generated test for fail skip branch
        request = MagicMock()
        db_instance = MagicMock()
        mock_db.return_value = db_instance

        ebox = MagicMock()
        ebox.mGetRequestObj.return_value = request
        ebox.mCheckConfigOption.return_value = {
            'vm_move_strict_errors': {'ERR1': 'False'}
        }

        exascale = ebCluExaScale(ebox)

        exascale.fail('ERR1', {'detail': 'issue'}, {'tip': 'advice'})

        request.mSetData.assert_called_once()
        db_instance.mUpdateRequest.assert_called_once_with(request)
        mock_warn.assert_called()
        mock_log_error.assert_called()

    @patch.dict('exabox.ovm.cluexascale.gExaDbXSError', {'ERR1': (456, 'cause {detail}', 'suggest {tip}')} , clear=True)
    @patch('exabox.ovm.cluexascale.ebGetDefaultDB')
    @patch('exabox.ovm.cluexascale.ebLogError')
    @patch('exabox.ovm.cluexascale.ebLogWarn')
    def test_fail_raises_when_strict(self, mock_warn, mock_log_error, mock_db):
        # Auto-generated test for fail strict branch
        request = MagicMock()
        db_instance = MagicMock()
        mock_db.return_value = db_instance

        ebox = MagicMock()
        ebox.mGetRequestObj.return_value = request
        ebox.mCheckConfigOption.return_value = {
            'vm_move_strict_errors': {'ERR1': 'True'}
        }

        exascale = ebCluExaScale(ebox)

        with self.assertRaises(ExacloudRuntimeError):
            exascale.fail('ERR1', {'detail': 'issue'}, {'tip': 'advice'})

        request.mSetData.assert_called_once()
        db_instance.mUpdateRequest.assert_called_once_with(request)
        mock_warn.assert_not_called()
        mock_log_error.assert_called()

    def test_basic_accessors(self):
        # Auto-generated test for mGetCluCtrl
        # Auto-generated test for mSetCluCtrl
        # Auto-generated test for mGetFailedStep
        controller = MagicMock()
        exascale = ebCluExaScale(controller)

        self.assertIs(exascale.mGetCluCtrl(), controller)
        new_controller = MagicMock()
        exascale.mSetCluCtrl(new_controller)
        self.assertIs(exascale.mGetCluCtrl(), new_controller)
        self.assertEqual(exascale.mGetFailedStep(), 'ALL')

    def test_copy_weblogic_cert_disabled_noop(self):
        # Auto-generated test for mCopyWeblogicCert
        _ebox = MagicMock()
        _ebox.mCheckSubConfigOption.return_value = "False"
        _exascale = ebCluExaScale(_ebox)

        with patch('exabox.ovm.cluexascale.os.path.exists') as _exists, \
             patch('exabox.ovm.cluexascale.connect_to_host') as _connect, \
             patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx")):
            self.assertIsNone(_exascale.mCopyWeblogicCert())

        _ebox.mCheckSubConfigOption.assert_called_once_with("weblogic_cert", "Enabled")
        _exists.assert_not_called()
        _connect.assert_not_called()

    def test_copy_weblogic_cert_downloads_and_copies(self):
        # Auto-generated test for mCopyWeblogicCert
        _ebox = MagicMock()
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mExecuteLocal.return_value = (0, "", "", "")
        _ebox.mReturnDom0DomUPair.return_value = [("dom0-a", "domu-a"), ("dom0-b", "domu-b")]

        _config = {
            ("weblogic_cert", "Enabled"): "True",
            ("weblogic_cert", "weblogic_cert_localpath"): "cert.pem",
            ("weblogic_cert", "weblogic_cert_oss_link"): "https://example.com/cert.pem",
            ("weblogic_cert", "weblogic_cert_vmpath"): "/remote/cert.pem",
        }
        _ebox.mCheckSubConfigOption.side_effect = lambda section, key: _config[(section, key)]

        _exascale = ebCluExaScale(_ebox)

        with patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx")), \
             patch('exabox.ovm.cluexascale.os.path.exists') as _exists, \
             patch('exabox.ovm.cluexascale.connect_to_host') as _connect:

            _exists_values = iter([False, True])

            def _exists_side_effect(path):
                try:
                    return next(_exists_values)
                except StopIteration:
                    return True

            _exists.side_effect = _exists_side_effect

            _nodes = []

            def _connect_side_effect(host, context, username="root"):
                _config = {'domu-a': False, 'domu-b': True}
                _node = MagicMock()
                _node.mFileExists.return_value = _config[host]
                _node.mCopyFile.return_value = None
                _ctx = MagicMock()
                _ctx.__enter__.return_value = _node
                _ctx.__exit__.return_value = False
                _nodes.append((host, _node))
                return _ctx

            _connect.side_effect = _connect_side_effect

            _exascale.mCopyWeblogicCert()

        _ebox.mExecuteLocal.assert_called_once_with('/usr/bin/curl https://example.com/cert.pem -o /base/cert.pem')
        self.assertEqual(len(_nodes), 2)
        _nodes_dict = dict(_nodes)
        _nodes_dict['domu-a'].mCopyFile.assert_called_once_with('/base/cert.pem', '/remote/cert.pem')
        _nodes_dict['domu-b'].mCopyFile.assert_not_called()

    def test_copy_weblogic_cert_download_failure_raises(self):
        # Auto-generated test for mCopyWeblogicCert
        _ebox = MagicMock()
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mExecuteLocal.return_value = (1, "", "", "error")

        _config = {
            ("weblogic_cert", "Enabled"): "True",
            ("weblogic_cert", "weblogic_cert_localpath"): "cert.pem",
            ("weblogic_cert", "weblogic_cert_oss_link"): "https://example.com/cert.pem",
            ("weblogic_cert", "weblogic_cert_vmpath"): "/remote/cert.pem",
        }
        _ebox.mCheckSubConfigOption.side_effect = lambda section, key: _config[(section, key)]

        _exascale = ebCluExaScale(_ebox)

        with patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx")), \
             patch('exabox.ovm.cluexascale.os.path.exists', side_effect=[False]) as _exists:
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mCopyWeblogicCert()

        _ebox.mExecuteLocal.assert_called_once()
        _exists.assert_called_once()

    def test_copy_weblogic_cert_missing_local_raises(self):
        # Auto-generated test for mCopyWeblogicCert
        _ebox = MagicMock()
        _ebox.mGetBasePath.return_value = "/base"

        _config = {
            ("weblogic_cert", "Enabled"): "True",
            ("weblogic_cert", "weblogic_cert_localpath"): "cert.pem",
            ("weblogic_cert", "weblogic_cert_oss_link"): "",
            ("weblogic_cert", "weblogic_cert_vmpath"): "/remote/cert.pem",
        }
        _ebox.mCheckSubConfigOption.side_effect = lambda section, key: _config[(section, key)]

        _exascale = ebCluExaScale(_ebox)

        with patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx")), \
             patch('exabox.ovm.cluexascale.os.path.exists') as _exists:

            _exists_values = iter([False, False])

            def _exists_side_effect(path):
                try:
                    return next(_exists_values)
                except StopIteration:
                    return False

            _exists.side_effect = _exists_side_effect

            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mCopyWeblogicCert()

        _ebox.mExecuteLocal.assert_not_called()

    def test_copy_weblogic_cert_remote_copy_failure_raises(self):
        # Auto-generated test for mCopyWeblogicCert
        _ebox = MagicMock()
        _ebox.mGetBasePath.return_value = "/base"
        _ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu")]

        _config = {
            ("weblogic_cert", "Enabled"): "True",
            ("weblogic_cert", "weblogic_cert_localpath"): "cert.pem",
            ("weblogic_cert", "weblogic_cert_oss_link"): "https://example.com/cert.pem",
            ("weblogic_cert", "weblogic_cert_vmpath"): "/remote/cert.pem",
        }
        _ebox.mCheckSubConfigOption.side_effect = lambda section, key: _config[(section, key)]

        _exascale = ebCluExaScale(_ebox)

        with patch('exabox.ovm.cluexascale.get_gcontext', return_value=Mock(name="gctx")), \
             patch('exabox.ovm.cluexascale.os.path.exists', side_effect=[True, True]), \
             patch('exabox.ovm.cluexascale.connect_to_host') as _connect:

            def _connect_side_effect(host, context, username="root"):
                _node = MagicMock()
                _node.mFileExists.return_value = False
                _node.mCopyFile.return_value = 1
                _ctx = MagicMock()
                _ctx.__enter__.return_value = _node
                _ctx.__exit__.return_value = False
                return _ctx

            _connect.side_effect = _connect_side_effect

            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mCopyWeblogicCert()

        _connect.assert_called_once()

if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end of file
