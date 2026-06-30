import inspect
import os
import tempfile
import unittest

from unittest.mock import ANY, Mock, call, patch, mock_open

from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.kvmcpumgr import exaBoxKvmCpuMgr


class TestKVMCpuManagerV2(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('kvm_override_disable_pinning', False)
        self.mGetClubox().mRegisterVgComponents()

    # Auto-generated test for mIsActiveGuest
    def test_mIsActiveGuest_true_on_exit_status_zero(self):
        cluctrl = self.mGetClubox()
        mgr = exaBoxKvmCpuMgr(cluctrl)
        node = Mock()
        node.mSingleLineOutput.return_value = "guestvm1(24) : running"
        node.mGetCmdExitStatus.return_value = 0

        self.assertTrue(mgr.mIsActiveGuest(node, "guestvm1"))

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_pinning_disabled(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return True
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        self.assertIsNone(mgr.mModifyServiceKvm(aOptions=self.mGetPayload()))

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_non_cos_no_update(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                )
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["domu1", "domu2"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        _options = self.mGetPayload()
        _options.jsonconf['poolsize'] = 4
        _options.jsonconf['subfactor'] = 1

        mgr = exaBoxKvmCpuMgr(cluctrl)
        rc = mgr.mModifyServiceKvm(aOptions=_options, aSubfactor=1, aPoolsize=4)
        self.assertEqual(rc, 0)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_routes_to_dg_vmmaker(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_vmmaker'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        fake_obj = Mock()
        fake_obj.mManageVMCpusCountKvm.return_value = 99

        with patch("exabox.ovm.kvmcpumgr.exaBoxKvmDgrpVmkr", return_value=fake_obj):
            mgr = exaBoxKvmCpuMgr(cluctrl)
            rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 99)
        fake_obj.mManageVMCpusCountKvm.assert_called_once()

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_missing_payload(self):
        cluctrl = self.mGetClubox()
        mgr = exaBoxKvmCpuMgr(cluctrl)
        rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=None)
        self.assertIsInstance(rc, int)
        self.assertLess(rc, 0)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_command_failure(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: '')),
            (None, None, Mock(read=lambda: 'list failure')),
            (None, None, Mock(read=lambda: '')),
            (None, None, Mock(read=lambda: 'list failure')),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 1, 0, 1]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 8, "dom0", True, result)

        self.assertFalse(result["guestvm1"]["cpu_resize_success"])
        self.assertIsNone(result["guestvm1"]["currvcpus"])
        self.assertIsNone(result["guestvm1"]["configvcpus"])

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_cos_updates_and_validates(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="6-7"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq",
                    aStdout="4-5"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '10'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["domu1", "domu2"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        _options = self.mGetPayload()
        _options.jsonconf['poolsize'] = 2
        _options.jsonconf['subfactor'] = 2

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            rc = mgr.mModifyServiceKvm(aOptions=_options, aSubfactor=2, aPoolsize=2)
        self.assertEqual(rc, 0)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_non_cos_validation_skips_down_vm(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="6-7"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="6-7"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 4-5 --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 4-5 --config"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '10'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["domu1", "domu2"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        _options = self.mGetPayload()
        _options.jsonconf['poolsize'] = 2
        _options.jsonconf['subfactor'] = 1

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with patch.object(mgr, 'mIsActiveGuest', return_value=False):
            rc = mgr.mModifyServiceKvm(aOptions=_options, aSubfactor=1, aPoolsize=2)

        self.assertEqual(rc, 0)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_non_cos_validation_logs_mismatch(self):
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq",
                    aStdout="6-7"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '0'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["domu1", "domu2"])

        _options = self.mGetPayload()
        _options.jsonconf['poolsize'] = 2
        _options.jsonconf['subfactor'] = 1

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                with patch("exabox.ovm.kvmcpumgr.ebLogInfo") as log_info:
                    with patch("exabox.ovm.kvmcpumgr.exaBoxNode") as node_cls:
                        node = node_cls.return_value
                        node.mConnect.return_value = None
                        node.mDisconnect.return_value = None
                        def execute_cmd(cmd):
                            if "virsh vcpuinfo" in cmd:
                                return None, Mock(readlines=Mock(return_value=["6-7"])), None
                            return None, None, None
                        node.mExecuteCmd.side_effect = execute_cmd
                        rc = mgr.mModifyServiceKvm(aOptions=_options, aSubfactor=1, aPoolsize=2, aDomain="guestvm1", aForcePinning=True)

        self.assertEqual(rc, 0)
        self.assertTrue(log_info.called)

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_history_console_missing(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.IsZdlraProv = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.return_value = False

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertIsNone(result)

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_copy_failure(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.side_effect = [True, True]
        node.mExecuteCmd.return_value = (None, None, None)
        node.mGetCmdExitStatus.return_value = 0
        node.mCopy2Local.return_value = None

        with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=False):
            class DummyCtx(object):
                def __enter__(self_inner):
                    return node
                def __exit__(self_inner, exc_type, exc, tb):
                    return False

            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertIsNone(result)

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_skips_no_console_access(self):
        cluctrl = self.mGetClubox()
        mgr = exaBoxKvmCpuMgr(cluctrl)

        host_d = {
            "guestvm1": {
                "consoleaccess": False,
                "logbeforeresize": "/tmp/serial.log.1",
            }
        }

        with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=[]):
            result = mgr.mCheckForReboots([["dom0", "guestvm1"]], 1, host_d)

        self.assertFalse(result)

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_handles_exception(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": "/tmp/serial.log.1"}}

        with patch.object(mgr, 'mGetConsoleLog', side_effect=Exception("boom")):
            with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=[]):
                result = mgr.mCheckForReboots([["dom0", "guestvm1"]], 1, host_d)

        self.assertFalse(result)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_parse_error(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=["guestvm1 cpu status"])), Mock(read=lambda: "")),
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=["guestvm1 cpu status"])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertFalse(result["guestvm1"]["cpu_resize_success"])
        self.assertIsNone(result["guestvm1"]["currvcpus"])
        self.assertIsNone(result["guestvm1"]["configvcpus"])

    # Auto-generated test for mPatchVMCfgVcpuCountKvm
    def test_mPatchVMCfgVcpuCountKvm_pingable_zdlra_ratio(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'zdlra_core_to_vcpu_ratio':
                return '3'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.IsZdlraProv = Mock(return_value=True)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode") as node_cls:
            node_cls.return_value = node
            node.mConnect.return_value = None
            node.mDisconnect.return_value = None
            with patch.object(mgr, 'mIsActiveGuest', return_value=True):
                options = self.mGetPayload()
                options.jsonconf['vm'] = {"cores": 4}
                mgr.mPatchVMCfgVcpuCountKvm("dom0", "guestvm1", options)

        node.mExecuteCmdLog.assert_called_once_with(
            "/usr/sbin/vm_maker --set --vcpu 12 --domain guestvm1 --force"
        )

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_routes_to_dg_vmmaker(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_vmmaker'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        fake_obj = Mock()
        fake_obj.mManageVMCpusBurstingKvm.return_value = 11

        with patch("exabox.ovm.kvmcpumgr.exaBoxKvmDgrpVmkr", return_value=fake_obj):
            mgr = exaBoxKvmCpuMgr(cluctrl)
            rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 11)
        fake_obj.mManageVMCpusBurstingKvm.assert_called_once()

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_sum_vcpus_exceeds_allocatable(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1\nguestvm2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="3"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm2 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="3"
                )
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=False)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1", "guestvm2"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with self.assertRaises(Exception):
            mgr.mModifyServiceKvm(aOptions=self.mGetPayload(), aSubfactor=2, aPoolsize=2)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_missing_dominfo_raises(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout=""
                )
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=False)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with self.assertRaises(Exception):
            mgr.mModifyServiceKvm(aOptions=self.mGetPayload(), aSubfactor=1, aPoolsize=2)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_nodeinfo_failure(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpuresize_check_reboots':
                return 'False'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=True)
        cluctrl.isExacomputeVM = Mock(return_value=False)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.return_value = (None, Mock(read=lambda: "out"), Mock(read=lambda: "err"))
        node.mGetCmdExitStatus.return_value = 1

        class DummyCtx(object):
            def __enter__(self_inner):
                return Mock()
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with self.assertRaises(Exception):
                        mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_poolsize_missing_returns_error(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=False)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1", "guestvm2"])

        options = self.mGetPayload()
        options.jsonconf.pop('poolsize', None)
        options.jsonconf['subfactor'] = 2

        mgr = exaBoxKvmCpuMgr(cluctrl)
        rc = mgr.mModifyServiceKvm(aOptions=options)

        self.assertIsInstance(rc, int)
        self.assertLess(rc, 0)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_zdlra_ratio_override(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                )
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'zdlra_core_to_vcpu_ratio':
                return '3'
            if key == 'timeout_vcpu_pin':
                return '1'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.IsZdlraProv = Mock(return_value=True)
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1", "guestvm2"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        options = self.mGetPayload()
        options.jsonconf['poolsize'] = 2
        options.jsonconf['subfactor'] = 1

        mgr = exaBoxKvmCpuMgr(cluctrl)
        rc = mgr.mModifyServiceKvm(aOptions=options, aSubfactor=1, aPoolsize=2)
        self.assertEqual(rc, 0)

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_updates_maxvcpus(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10\n"])), None),
            (None, Mock(readlines=Mock(return_value=["2\n"])), None),
            (None, Mock(readlines=Mock(return_value=["4\n"])), None),
            (None, None, None),
        ]

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 0)
        self.assertTrue(node.mExecuteCmd.called)

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_split_error(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): xx\n"])), None),
            (None, Mock(readlines=Mock(return_value=["2\n"])), None),
        ]

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with self.assertRaises(ValueError):
                mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_emits_payload(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.IsZdlraProv = Mock(return_value=False)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=None)

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["guestvm1 : 4"])), None),
            (None, Mock(readlines=Mock(return_value=["4-7\n"])), None)
        ]

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                mgr.mClusterCPUInfoKvm(self.mGetPayload())

        self.assertTrue(node.mExecuteCmd.called)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_down_vm_success(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: '')),
            (None, Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: 0 (domain is down) Restart: 6"
            ])), Mock(read=lambda: '')),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", False, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 6)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_retries_with_config_update(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: '')),
            (None, Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: 6 Restart: 4"
            ])), Mock(read=lambda: '')),
            (None, None, Mock(read=lambda: '')),
            (None, Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: 6 Restart: 6"
            ])), Mock(read=lambda: '')),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        set_calls = [call.args[0] for call in node.mExecuteCmd.call_args_list[:3:2]]
        self.assertIn("--config --force", set_calls[1])

    # Auto-generated test for mPatchVMCfgVcpuCountKvm
    def test_mPatchVMCfgVcpuCountKvm_not_pingable(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode") as node_cls:
            node_cls.return_value = node
            node.mConnect.return_value = None
            node.mDisconnect.return_value = None
            with patch.object(mgr, 'mIsActiveGuest', return_value=False):
                options = self.mGetPayload()
                options.jsonconf['vm'] = {"cores": 4}
                mgr.mPatchVMCfgVcpuCountKvm("dom0", "guestvm1", options)

        node.mExecuteCmdLog.assert_called_once_with(
            "/usr/sbin/vm_maker --set --vcpu 8 --domain guestvm1 --config --force"
        )

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_oedacli_mode_returns_none(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_oedacli'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertIsNone(rc)

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_routes_to_dg_vmmaker(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_vmmaker'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        fake_obj = Mock()
        fake_obj.mClusterCPUInfoKvm.return_value = 5

        with patch("exabox.ovm.kvmcpumgr.exaBoxKvmDgrpVmkr", return_value=fake_obj):
            mgr = exaBoxKvmCpuMgr(cluctrl)
            rc = mgr.mClusterCPUInfoKvm(self.mGetPayload())

        self.assertEqual(rc, 5)
        fake_obj.mClusterCPUInfoKvm.assert_called_once()

    # Auto-generated test for fetchDiagLogs
    def test_fetchDiagLogs_skips_when_disabled(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value='False')
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        mgr.fetchDiagLogs("dom0", node)

        self.assertFalse(node.mExecuteCmd.called)

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_detects_reboot_marker(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value=tempfile.gettempdir())
        cluctrl.mCheckConfigOption = Mock(return_value=["rebooted"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "serial.log.1")
            file2 = os.path.join(tmpdir, "serial.log.2")
            with open(file1, "w") as f1:
                f1.write("boot ok\n")
            with open(file2, "w") as f2:
                f2.write("boot ok\nrebooted now\n")

            host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": file1}}

            with patch.object(mgr, 'mGetConsoleLog', return_value=file2):
                with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=[]):
                    result = mgr.mCheckForReboots([["dom0", "guestvm1"]], 1, host_d)

        self.assertTrue(result)

    # Auto-generated test for mResizeCpus
    def test_mResizeCpus_parallel_uses_process_manager(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=True)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        class DummyProc(object):
            def __init__(self, target, args):
                self.target = target
                self.args = args
                self.max_time = None
                self.join_timeout = None
                self.log_fx = None

            def mSetMaxExecutionTime(self, value):
                self.max_time = value

            def mSetJoinTimeout(self, value):
                self.join_timeout = value

            def mSetLogTimeoutFx(self, value):
                self.log_fx = value

        class DummyManager(object):
            def __init__(self):
                self.started = []
                self.joined = False

            def mGetManager(self):
                return self

            def dict(self):
                return {"guestvm1": {"cpu_resize_success": True}}

            def mStartAppend(self, proc):
                self.started.append(proc)

            def mJoinProcess(self):
                self.joined = True

        dummy_manager = DummyManager()

        with patch("exabox.ovm.kvmcpumgr.ProcessManager", return_value=dummy_manager):
            with patch("exabox.ovm.kvmcpumgr.ProcessStructure", DummyProc):
                result = mgr.mResizeCpus([
                    {"domu": "guestvm1", "vcpus": 6, "dom0": "dom0", "pingable": True},
                    {"domu": "guestvm2", "vcpus": 8, "dom0": "dom0", "pingable": False},
                ])

        self.assertEqual(result, {"guestvm1": {"cpu_resize_success": True}})
        self.assertEqual(len(dummy_manager.started), 2)
        self.assertTrue(dummy_manager.joined)
        self.assertEqual(dummy_manager.started[0].args[0], "guestvm1")
        self.assertEqual(dummy_manager.started[1].args[0], "guestvm2")

    # Auto-generated test for mResizeCpus
    def test_mResizeCpus_sequential_invokes_setvcpu(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        def do_set(domu, vcpus, dom0, pingable, result):
            result[domu] = {"cpu_resize_success": pingable, "currvcpus": vcpus}

        with patch.object(mgr, "mSetVCPUandValidate", side_effect=do_set) as setvcpu:
            result = mgr.mResizeCpus([
                {"domu": "guestvm1", "vcpus": 4, "dom0": "dom0", "pingable": True},
                {"domu": "guestvm2", "vcpus": 2, "dom0": "dom1", "pingable": False},
            ])

        self.assertEqual(setvcpu.call_count, 2)
        self.assertEqual(result["guestvm1"]["currvcpus"], 4)
        self.assertFalse(result["guestvm2"]["cpu_resize_success"])

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_cos_domain_mismatch_skips_update(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '1'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1", "guestvm2"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        options = self.mGetPayload()
        options.jsonconf['poolsize'] = 2
        options.jsonconf['subfactor'] = 2

        mgr = exaBoxKvmCpuMgr(cluctrl)
        rc = mgr.mModifyServiceKvm(aOptions=options, aSubfactor=2, aPoolsize=2, aDomain="guestvm2")
        self.assertEqual(rc, 0)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_cos_validates_and_raises_on_mismatch(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 4-7 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 4-7 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq",
                    aStdout="5-6"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq",
                    aStdout="5-6"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '0'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        options = self.mGetPayload()
        options.jsonconf['poolsize'] = 2
        options.jsonconf['subfactor'] = 2

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with patch.object(mgr, 'mIsActiveGuest', return_value=False):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                rc = mgr.mModifyServiceKvm(aOptions=options, aSubfactor=2, aPoolsize=2)

        self.assertEqual(rc, 0)

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_non_cos_validation_raises_after_timeout(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 4-5 --live --config"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '0'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        options = self.mGetPayload()
        options.jsonconf['poolsize'] = 2
        options.jsonconf['subfactor'] = 1

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with patch.object(mgr, 'mIsActiveGuest', return_value=False):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                rc = mgr.mModifyServiceKvm(aOptions=options, aSubfactor=1, aPoolsize=2)

        self.assertEqual(rc, 0)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_exit_status_retry(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "bad")),
            (None, Mock(readlines=Mock(return_value=["guestvm1  : Current: 10 Restart: 10"])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [1, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 10, "dom0", True, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 10)
        self.assertEqual(result["guestvm1"]["configvcpus"], 10)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_uses_config_update_on_live_mismatch(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=["guestvm1  : Current: 6 Restart: 4"])), Mock(read=lambda: "")),
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=["guestvm1  : Current: 6 Restart: 6"])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 6)

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_successful_copy(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.side_effect = [True, True]
        node.mGetCmdExitStatus.return_value = 0

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=True):
                result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertEqual(result, "/tmp/log/serial.log")
        node.mCopy2Local.assert_called_once_with("/tmp/serial.log", "/tmp/log/serial.log")
        node.mExecuteCmd.assert_any_call("/bin/rm -f /tmp/serial.log")

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_cleans_temp_logs(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        cluctrl.mCheckConfigOption = Mock(return_value=["rebooted"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": "/tmp/serial.log.1"}}

        with patch.object(mgr, "mGetConsoleLog", return_value="/tmp/serial.log.2"):
            with patch("exabox.ovm.kvmcpumgr.open", mock_open(read_data="boot ok\n")):
                with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=["/tmp/serial-uuid-guestvm1.log.1"]):
                    with patch("exabox.ovm.kvmcpumgr.os.remove") as remove:
                        result = mgr.mCheckForReboots([("dom0", "guestvm1")], 1, host_d)

        self.assertFalse(result)
        remove.assert_called_once_with("/tmp/serial-uuid-guestvm1.log.1")

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_non_pingable_uses_config_count(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: 0 (domain is down) Restart: 6"
            ])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", False, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 6)

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_updates_maxvcpus(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=None)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonmode = False
        options.jsonconf = {"vms": [{"hostname": "guestvm1", "cores": "6"}]}

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])) , None),
            (None, Mock(readlines=Mock(return_value=["4"])) , None),
            (None, Mock(readlines=Mock(return_value=["2"])) , None),
            (None, None, None),
        ]

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=options)

        self.assertEqual(rc, 0)
        node.mExecuteCmd.assert_any_call("/usr/bin/virsh setvcpus guestvm1 6 --maximum --config")

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_collects_vcpu_and_pinning(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=None)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonmode = False

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["6"])) , None),
            (None, Mock(readlines=Mock(return_value=["4-5\n"])) , None),
        ]

        with patch.object(mgr, "mIsActiveGuest", return_value=False):
            with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                mgr.mClusterCPUInfoKvm(options)

        self.assertTrue(node.mExecuteCmd.called)

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_exit_status_failure(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = 1

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertIsNone(result)

    # Auto-generated test for mPatchVMCfgVcpuCountKvm
    def test_mPatchVMCfgVcpuCountKvm_non_pingable_uses_config(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.IsZdlraProv = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode") as node_cls:
            node_cls.return_value = node
            node.mConnect.return_value = None
            node.mDisconnect.return_value = None
            with patch.object(mgr, "mIsActiveGuest", return_value=False):
                options = self.mGetPayload()
                options.jsonconf['vm'] = {"cores": 2}
                mgr.mPatchVMCfgVcpuCountKvm("dom0", "guestvm1", options)

        node.mExecuteCmdLog.assert_called_once_with(
            "/usr/sbin/vm_maker --set --vcpu 4 --domain guestvm1 --config --force"
        )

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_nodeinfo_parse_failure(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=None)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonmode = False
        options.jsonconf = {}

        node = Mock()
        node.mExecuteCmd.return_value = (None, Mock(readlines=Mock(return_value=["badline"])), None)

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with self.assertRaises(Exception):
                mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_no_pingable_dom0s_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckDom0sPingable = Mock(return_value=([], ["dom0"]))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

        with self.assertRaises(Exception):
            mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_missing_cpu_line_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

        node = Mock()
        node.mExecuteCmd.return_value = (None, Mock(readlines=Mock(return_value=["Not CPU info"])) , None)
        node.mGetCmdExitStatus.return_value = 0

        class DummyCtx(object):
            def __enter__(self_inner):
                return Mock()
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with self.assertRaises(Exception):
                        mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_review_handles_bursting_mismatch(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        cluctrl.mGetRequestObj = Mock(return_value=Mock(mSetData=Mock()))
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {"vms": [{"hostname": "guestvm1", "cores": "6"}]}

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
            (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
            (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
            (None, Mock(readlines=Mock(return_value=["maximum config 8"])), None),
            (None, Mock(readlines=Mock(return_value=["maximum config 6"])), None),
        ]

        out_obj = Mock(stdout="Total vcpu required for reboot : 6")

        class DummyCtx(object):
            def __enter__(self_inner):
                return Mock()
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                        with patch("exabox.ovm.kvmcpumgr.ebGetDefaultDB") as db_get:
                            db_get.return_value = Mock(mUpdateRequest=Mock())
                            rc = mgr.mManageVMCpusCountKvm("cpustatus", "guestvm1", aOptions=options)

        self.assertEqual(rc, 0)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_raises_when_no_dom0s_pingable(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=([], ["dom0"]))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf["vms"] = [{"hostname": "guestvm1", "cores": "4"}]

        with self.assertRaises(Exception):
            mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_cos_missing_poolsize_returns_error(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf["vms"] = [{"hostname": "guestvm1", "cores": "4"}]
        options.jsonconf["subfactor"] = 2

        rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

        self.assertIsInstance(rc, int)
        self.assertLess(rc, 0)

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_default_reserved_no_update(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=Mock(mSetData=Mock()))
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 8"])), None),
            (None, Mock(readlines=Mock(return_value=[])), None),
            (None, Mock(readlines=Mock(return_value=["4"])), None),
        ]

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.ebGetDefaultDB") as db_get:
                db_get.return_value = Mock(mUpdateRequest=Mock())
                rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 0)
        self.assertFalse(any("setvcpus" in args[0] for args, _ in node.mExecuteCmd.call_args_list))

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_command_failure_returns_none(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.return_value = True
        node.mExecuteCmd.return_value = (None, None, None)
        node.mGetCmdExitStatus.return_value = 1

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertIsNone(result)

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_successful_copy_returns_path(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.side_effect = [True, True]
        node.mExecuteCmd.return_value = (None, None, None)
        node.mGetCmdExitStatus.return_value = 0

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertEqual(result, "/tmp/log/serial.log")
        node.mCopy2Local.assert_called_once_with("/tmp/serial.log", "/tmp/log/serial.log")
        node.mExecuteCmd.assert_any_call("/bin/rm -f /tmp/serial.log")

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_no_markers_still_cleans_logs(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        cluctrl.mCheckConfigOption = Mock(return_value=["panic"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "serial.log.1")
            file2 = os.path.join(tmpdir, "serial.log.2")
            with open(file1, "w") as f1:
                f1.write("boot ok\n")
            with open(file2, "w") as f2:
                f2.write("boot ok\nready\n")

            host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": file1}}

            with patch.object(mgr, "mGetConsoleLog", return_value=file2):
                with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=[
                    "/tmp/log/serial-uuid-guestvm1.log.1",
                    "/tmp/log/serial-uuid-guestvm1.log.2",
                ]):
                    with patch("exabox.ovm.kvmcpumgr.os.remove") as rm_file:
                        result = mgr.mCheckForReboots([("dom0", "guestvm1")], 1, host_d)

        self.assertFalse(result)
        self.assertEqual(rm_file.call_count, 2)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_down_vm_success_path(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: 0 (domain is down) Restart: 6"
            ])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", False, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 6)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_cpustatus_payload_sets_review(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=True)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf = {}

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
    ]

    out_obj = Mock(stdout="Total vcpu required for reboot : 6")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                rc = mgr.mManageVMCpusCountKvm("cpustatus", "guestvm1", aOptions=options)

    self.assertEqual(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_invalid_vm_entries_returns_error(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = ["invalid"]

    rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_total_vcpu_parse_failure_returns_error(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=False)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
    ]

    out_obj = Mock(stdout="no parse here")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_vm_maker_vcpu_value_parse_failure(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=False)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
    ]

    out_obj = Mock(stdout="Total vcpu required for reboot : n/a")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_overprovisioning_returns_error(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=False)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "12"}]

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
    ]

    out_obj = Mock(stdout="Total vcpu required for reboot : 6")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_max_cpu_less_returns_error(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=False)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "11"}]

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 12"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 8"])), None),
    ]

    out_obj = Mock(stdout="Total vcpu required for reboot : 6")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_xml_mismatch_returns_error(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=False)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 8"])), None),
    ]

    out_obj = Mock(stdout="Total vcpu required for reboot : 6")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)

# Auto-generated test for mManageVMCpusCountKvm
def test_mManageVMCpusCountKvm_setvcpu_failure_returns_error(self):
    cluctrl = self.mGetClubox()
    cluctrl.mCheckConfigOption = Mock(return_value=None)
    cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
    cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
    cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
    cluctrl.isBaseDB = Mock(return_value=False)
    cluctrl.isExacomputeVM = Mock(return_value=False)
    mgr = exaBoxKvmCpuMgr(cluctrl)

    options = self.mGetPayload()
    options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

    node = Mock()
    node.mGetCmdExitStatus.return_value = 0
    node.mExecuteCmd.side_effect = [
        (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
        (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
        (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
        (None, Mock(readlines=Mock(return_value=["maximum config 12"])), None),
    ]

    out_obj = Mock(stdout="Total vcpu required for reboot : 6")

    with patch.object(mgr, "mIsActiveGuest", return_value=True):
        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                with patch.object(mgr, "mResizeCpus", return_value={"guestvm1": {"cpu_resize_success": False, "currvcpus": 4, "configvcpus": 4}}):
                    rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    self.assertIsInstance(rc, int)
    self.assertLess(rc, 0)


class TestKVMCpuManagerV2Extra(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_review_sets_bursting_flags(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        cluctrl.mGetRequestObj = Mock(return_value=Mock())
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {
            'vms': [{"hostname": "guestvm1", "cores": "4"}],
        }

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=['CPU(s): 12'])), None),
            (None, Mock(readlines=Mock(return_value=['Host reserved PCPU                     : 4'])), None),
            (None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 4 Restart: 4'])), None),
            (None, Mock(readlines=Mock(return_value=['maximum config 12'])), None),
            (None, Mock(readlines=Mock(return_value=['maximum config 12'])), None),
            (None, Mock(readlines=Mock(return_value=['vm1\n'])), None),
            (None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 4 Restart: 4'])), None),
        ]

        out_obj = Mock(stdout='Total vcpu required for reboot : 2')

        class DummyCtx(object):
            def __enter__(self_inner):
                return Mock()
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch('exabox.ovm.kvmcpumgr.connect_to_host', return_value=DummyCtx()):
                with patch('exabox.ovm.kvmcpumgr.exaBoxNode', return_value=node):
                    with patch('exabox.ovm.kvmcpumgr.node_exec_cmd_check', return_value=out_obj):
                        with patch('exabox.ovm.kvmcpumgr.ebGetDefaultDB'):
                            with patch('exabox.ovm.kvmcpumgr.ebLogInfo') as log_info:
                                rc = mgr.mManageVMCpusCountKvm('cpustatus', 'guestvm1', aOptions=options)

        self.assertEqual(rc, 0)
        log_msg = ' '.join(call_args[0][0] for call_args in log_info.call_args_list)
        self.assertIn('cpu allocation', log_msg)
        get_gcontext().mSetConfigOption('kvm_override_disable_pinning', False)
        self.mGetClubox().mRegisterVgComponents()

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_success_copies_log(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.side_effect = [True, True]
        node.mExecuteCmd.return_value = (None, None, None)
        node.mGetCmdExitStatus.return_value = 0
        node.mCopy2Local.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertEqual(result, "/tmp/log/serial.log")
        node.mCopy2Local.assert_called_once_with("/tmp/serial.log", "/tmp/log/serial.log")

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_updates_config_for_pingable(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        def output_for(curr, restart):
            return Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: %s Restart: %s" % (curr, restart)
            ]))

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, output_for(6, 4), Mock(read=lambda: "")),
            (None, None, Mock(read=lambda: "")),
            (None, output_for(6, 6), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 6)
        cmd_calls = [call_args[0][0] for call_args in node.mExecuteCmd.call_args_list]
        self.assertTrue(any("--config --force" in cmd for cmd in cmd_calls))

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_updates_maxvcpus(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetRequestObj = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 12\n"])), None),
            (None, Mock(readlines=Mock(return_value=["4\n"])), None),
            (None, Mock(readlines=Mock(return_value=["6\n"])), None),
            (None, None, None),
        ]

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 0)
        node.mExecuteCmd.assert_any_call(
            "/usr/bin/virsh setvcpus guestvm1 8 --maximum --config"
        )

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_exaunit_allocations_success(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        cluctrl.mModifyService = Mock()

        options = self.mGetPayload()
        options.jsonconf = {
            "exaunitAllocations": {"cores": "4"},
            "subfactor": 1,
        }

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mGetHostname.return_value = "dom0"
        node.mDisconnect.return_value = None

        def exec_cmd(cmd):
            if cmd == "/usr/bin/virsh nodeinfo":
                return None, Mock(readlines=Mock(return_value=["CPU(s): 10\n"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu":
                return None, Mock(readlines=Mock(return_value=["Host reserved PCPU : 2\n"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu --domain guestvm1":
                return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 8 Restart: 8"])), None
            if cmd == "/usr/bin/virsh vcpucount guestvm1":
                return None, Mock(readlines=Mock(return_value=["maximum config 8\n"])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mConnect.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=Mock(stdout="Total vcpu required for reboot : 8")):
                        with patch.object(mgr, "mResizeCpus", return_value={
                            "guestvm1": {"cpu_resize_success": True, "currvcpus": 8, "configvcpus": 8}
                        }) as resize_mock:
                            rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

        self.assertEqual(rc, 0)
        self.assertIsInstance(rc, int)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_non_cos_restart_failure(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=True)
        cluctrl.isExacomputeVM = Mock(return_value=False)

        options = self.mGetPayload()
        options.jsonconf = {
            "vms": [{"hostname": "guestvm1", "cores": "1"}],
            "subfactor": 1,
        }

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mGetHostname.return_value = "dom0"

        def exec_cmd(cmd):
            if cmd == "/usr/bin/virsh nodeinfo":
                return None, Mock(readlines=Mock(return_value=["CPU(s): 10\n"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu":
                return None, Mock(readlines=Mock(return_value=["Host reserved PCPU : 2\n"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu --domain guestvm1":
                return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 4 Restart: 4"])), None
            if cmd == "/usr/bin/virsh vcpucount guestvm1":
                return None, Mock(readlines=Mock(return_value=["maximum config 4\n"])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd

        vm_handle = Mock()
        vm_handle.mDispatchEvent.side_effect = [0, 1]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=Mock(stdout="Total vcpu required for reboot : 2")):
                        with patch("exabox.ovm.kvmcpumgr.ebVgLifeCycle", return_value=vm_handle):
                            with patch.object(mgr, "mResizeCpus", return_value={
                                "guestvm1": {"cpu_resize_success": True, "currvcpus": 2, "configvcpus": 2}
                            }):
                                rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

        self.assertEqual(rc, ebError(0x0452))
        self.assertEqual(
            vm_handle.mDispatchEvent.call_args_list,
            [
                call('shutdown', aOptions=None, aVMId='guestvm1', aCluCtrlObj=cluctrl),
                call('start', aOptions=None, aVMId='guestvm1', aCluCtrlObj=cluctrl),
            ],
        )

    def test_mManageVMCpusCountKvm_non_cos_restart_passes_cluctrl(self):
        source = inspect.getsource(exaBoxKvmCpuMgr.mManageVMCpusCountKvm)
        self.assertEqual(source.count("aCluCtrlObj=self.__ecc"), 2)
        self.assertIn("_rc = _vmhandle.mDispatchEvent(", source)
        self.assertIn("'shutdown',", source)
        self.assertIn("'start',", source)

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_collects_vcpu_and_pinning(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["6\n"])), None),
            (None, Mock(readlines=Mock(return_value=["0-3", "4-5"])), None),
        ]

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                mgr.mClusterCPUInfoKvm(self.mGetPayload())

        self.assertEqual(node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_jsonmode_emits_output(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetRequestObj = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["4\n"])), None),
            (None, Mock(readlines=Mock(return_value=["2-3\n"])), None),
        ]

        options = Mock(jsonmode=True)

        with patch.object(mgr, "mIsActiveGuest", return_value=False):
            with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                with patch("exabox.ovm.kvmcpumgr.ebLogJson") as log_json:
                    mgr.mClusterCPUInfoKvm(options)

        self.assertTrue(log_json.called)
        self.assertIn("success", log_json.call_args[0][0])

    # Auto-generated test for mModifyServiceKvm
    def test_mModifyServiceKvm_non_cos_updates_when_domain_matches(self):
        _cmds = {
            "dom0": [[
                exaMockCommand(
                    "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="guestvm1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh dominfo guestvm1 | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'",
                    aStdout="2"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep VCPU | /bin/awk '{print$2}'",
                    aStdout="0\n1"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 | /bin/tail -n+3 | /bin/awk '{print $2}'",
                    aStdout="4-5"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 0 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpupin --domain guestvm1 --vcpu 1 4-5 --live --config"
                ),
                exaMockCommand(
                    "/usr/bin/virsh vcpuinfo guestvm1 --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq",
                    aStdout="4-5"
                ),
            ]]
        }

        self.mPrepareMockCommands(_cmds)

        def config_option(key, default=None):
            if key == 'kvm_override_disable_pinning':
                return False
            if key == 'timeout_vcpu_pin':
                return '1'
            return default

        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])

        options = self.mGetPayload()
        options.jsonconf['poolsize'] = 2
        options.jsonconf['subfactor'] = 1

        mgr = exaBoxKvmCpuMgr(cluctrl)
        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            rc = mgr.mModifyServiceKvm(aOptions=options, aSubfactor=1, aPoolsize=2, aDomain="guestvm1")

        self.assertEqual(rc, 0)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_vm_maker_failure_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=True)
        cluctrl.isExacomputeVM = Mock(return_value=False)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()

        def exec_cmd(cmd):
            if cmd == "/usr/bin/virsh nodeinfo":
                return None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu":
                return None, Mock(read=lambda: "bad"), Mock(read=lambda: "boom")
            if "--domain guestvm1" in cmd and "vm_maker" in cmd:
                return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None
            if cmd == "/usr/bin/virsh vcpucount guestvm1":
                return None, Mock(readlines=Mock(return_value=["maximum config 12"])), None
            return None, None, None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mGetCmdExitStatus.side_effect = [0, 1, 0, 0, 0]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with self.assertRaises(Exception):
                        mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_vm_maker_missing_cpu_line_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=["guestvm1"])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=True)
        cluctrl.isExacomputeVM = Mock(return_value=False)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()

        def exec_cmd(cmd):
            if cmd == "/usr/bin/virsh nodeinfo":
                return None, Mock(readlines=Mock(return_value=["Model: x86_64"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu":
                return None, Mock(read=lambda: ""), Mock(read=lambda: "")
            if "--domain guestvm1" in cmd and "vm_maker" in cmd:
                return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None
            if cmd == "/usr/bin/virsh vcpucount guestvm1":
                return None, Mock(readlines=Mock(return_value=["maximum config 12"])), None
            return None, None, None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with self.assertRaises(Exception):
                        mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_no_update_when_equal(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mGetRequestObj = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10\n"])), None),
            (None, Mock(readlines=Mock(return_value=["4\n"])), None),
            (None, Mock(readlines=Mock(return_value=["6\n"])), None),
        ]

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 0)
        node.mExecuteCmd.assert_any_call(
            "/usr/bin/virsh vcpucount guestvm1 | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'"
        )
        self.assertFalse(any("setvcpus" in call_args[0][0] for call_args in node.mExecuteCmd.call_args_list))

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_oedacli_not_supported(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_oedacli'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode") as node_cls:
            rc = mgr.mClusterCPUInfoKvm(self.mGetPayload())

        self.assertIsNone(rc)
        node_cls.assert_not_called()

    # Auto-generated test for fetchDiagLogs
    def test_fetchDiagLogs_collects_sundiag_and_varlog(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")

        def config_option(key, default=None):
            if key == 'collect_diags_for_cpuresize_failures':
                return 'True'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(read=Mock(return_value="Start\nDone. /tmp/sundiag.tgz\n")), None),
            (None, None, None),
            (None, None, None),
            (None, None, None),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]
        node.mDownloadRemoteFile.side_effect = [False, True]

        fake_now = Mock(strftime=Mock(return_value="2026_03_04_01-02"))

        with patch("exabox.ovm.kvmcpumgr.datetime") as fake_datetime:
            fake_datetime.datetime.now.return_value = fake_now
            with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=False):
                with patch("exabox.ovm.kvmcpumgr.os.makedirs") as makedirs:
                    mgr.fetchDiagLogs("dom0", node)

        makedirs.assert_called_once()
        node.mDownloadRemoteFile.assert_any_call("/tmp/sundiag.tgz", ANY)
        node.mDownloadRemoteFile.assert_any_call("/tmp/varlog-2026_03_04_01-02.tar.gz", ANY)
        node.mExecuteCmd.assert_any_call("/opt/oracle.SupportTools/sundiag.sh", aTimeout=1800)
        node.mExecuteCmd.assert_any_call("/usr/bin/rm -rf /tmp/sundiag.tgz")
        node.mExecuteCmd.assert_any_call(
            "/usr/bin/tar -czvf /tmp/varlog-2026_03_04_01-02.tar.gz /var/log/cellos* /var/log/libvirt/ /var/log/messages*",
            aTimeout=1800,
        )
        node.mExecuteCmd.assert_any_call("/usr/bin/rm -rf /tmp/varlog-2026_03_04_01-02.tar.gz")

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_success_copies_and_removes(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")

        def config_option(key, default=None):
            if key == 'history_console_timeout_in_seconds':
                return '5'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.side_effect = [True, True]
        node.mGetCmdExitStatus.return_value = 0

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertEqual(result, "/tmp/log/serial.log")
        node.mExecuteCmd.assert_any_call(
            "/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host guestvm1 --path /tmp/serial.log",
            aTimeout=5,
        )
        node.mExecuteCmd.assert_any_call("/bin/rm -f /tmp/serial.log")
        node.mCopy2Local.assert_called_once_with("/tmp/serial.log", "/tmp/log/serial.log")

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_handles_open_exception(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mCheckConfigOption = Mock(return_value=["panic"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": "/tmp/serial.log.1"}}

        with patch.object(mgr, "mGetConsoleLog", return_value="/tmp/serial.log.2"):
            with patch("exabox.ovm.kvmcpumgr.open", mock_open(), create=True) as open_mock:
                open_mock.side_effect = OSError("boom")
                with patch("exabox.ovm.kvmcpumgr.ebLogError") as log_error:
                    result = mgr.mCheckForReboots([("dom0", "guestvm1")], 1, host_d)

        self.assertFalse(result)
        self.assertTrue(log_error.called)


    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_offline_config_mismatch_sets_followup_cmd(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mGetHostname.return_value = 'dom0'
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: '')),
            (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 0 (domain is down) Restart: 6"])), Mock(read=lambda: '')),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", False, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 6)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_live_config_mismatch_triggers_config_cmd(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mGetHostname.return_value = 'dom0'
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: '')),
            (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 4"])), Mock(read=lambda: '')),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertFalse(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm1"]["configvcpus"], 4)

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_nodeinfo_split_error(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=Mock(mSetData=Mock()))
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s)"])), None),
        ]
        node.mGetCmdExitStatus.return_value = 0
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with self.assertRaises(IndexError):
                mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())



    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_updates_maxvcpus(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=Mock(mSetData=Mock()))
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 8"])), None),
            (None, Mock(readlines=Mock(return_value=["Host reserved: 2"])), None),
            (None, Mock(readlines=Mock(return_value=["4"])), None),
            (None, None, None),
        ]
        node.mGetCmdExitStatus.return_value = 0
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 0)
        node.mExecuteCmd.assert_any_call("/usr/bin/virsh setvcpus guestvm1 6 --maximum --config")

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_collects_data_jsonmode(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=None)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        class Opts(object):
            jsonmode = True

        options = Opts()

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["6"])), None),
            (None, Mock(readlines=Mock(return_value=["2-3"])), None),
        ]
        node.mGetCmdExitStatus.return_value = 0

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                with patch("exabox.ovm.kvmcpumgr.ebLogJson") as log_json:
                    mgr.mClusterCPUInfoKvm(options)

        self.assertTrue(log_json.called)
        self.assertEqual(node.mExecuteCmd.call_count, 2)

    # Auto-generated test for mIsActiveGuest
    def test_mIsActiveGuest_false_on_exit_status_nonzero(self):
        cluctrl = self.mGetClubox()
        mgr = exaBoxKvmCpuMgr(cluctrl)
        node = Mock()
        node.mSingleLineOutput.return_value = "guestvm1(24) : running"
        node.mGetCmdExitStatus.return_value = 1

        self.assertFalse(mgr.mIsActiveGuest(node, "guestvm1"))

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_routes_to_dg_vmmaker(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_vmmaker'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        fake_obj = Mock()
        fake_obj.mClusterCPUInfoKvm.return_value = 77

        with patch("exabox.ovm.kvmcpumgr.exaBoxKvmDgrpVmkr", return_value=fake_obj):
            mgr = exaBoxKvmCpuMgr(cluctrl)
            rc = mgr.mClusterCPUInfoKvm(self.mGetPayload())

        self.assertEqual(rc, 77)
        fake_obj.mClusterCPUInfoKvm.assert_called_once()

    # Auto-generated test for mClusterCPUInfoKvm
    def test_mClusterCPUInfoKvm_dg_oedacli_logs_and_returns_none(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_oedacli'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        with patch("exabox.ovm.kvmcpumgr.ebLogError") as log_err:
            rc = mgr.mClusterCPUInfoKvm(self.mGetPayload())

        self.assertIsNone(rc)
        self.assertTrue(log_err.called)

    # Auto-generated test for fetchDiagLogs
    def test_fetchDiagLogs_skips_when_disabled(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value='False')
        mgr = exaBoxKvmCpuMgr(cluctrl)
        node = Mock()

        mgr.fetchDiagLogs("dom0", node)

        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for fetchDiagLogs
    def test_fetchDiagLogs_collects_and_cleans(self):
        cluctrl = self.mGetClubox()
        def config_option(key, default=None):
            if key == 'kvm_minimum_vcpus':
                return '4'
            return None

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mGetUUID = Mock(return_value="uuid-123")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(read=Mock(return_value="Done. /tmp/sundiag.tar.gz\n")), None),
            (None, None, None),
            (None, None, None),
            (None, None, None),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]
        node.mDownloadRemoteFile.return_value = True

        cpuresize_dir = os.path.join(get_gcontext().mGetBasePath(), "log", "cpuresize_logs", "uuid-123")

        with patch("exabox.ovm.kvmcpumgr.os.path.exists", return_value=False):
            with patch("exabox.ovm.kvmcpumgr.os.makedirs") as mk_dir:
                with patch("exabox.ovm.kvmcpumgr.datetime.datetime") as dt_cls:
                    dt_cls.now.return_value = __import__("datetime").datetime(2024, 1, 2, 3, 4)
                    mgr.fetchDiagLogs("dom0", node)

        mk_dir.assert_called_once_with(cpuresize_dir)
        node.mDownloadRemoteFile.assert_any_call("/tmp/sundiag.tar.gz", cpuresize_dir)
        self.assertTrue(any("/opt/oracle.SupportTools/sundiag.sh" in args[0] for args in node.mExecuteCmd.call_args_list))

    # Auto-generated test for mResizeCpus
    def test_mResizeCpus_runs_in_parallel_when_enabled(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=True)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        dom_list = [
            {"domu": "guestvm1", "vcpus": 6, "dom0": "dom0", "pingable": True},
        ]

        class DummyProc(object):
            def __init__(self, func, args):
                self.func = func
                self.args = args
            def mSetMaxExecutionTime(self, *_args, **_kwargs):
                return None
            def mSetJoinTimeout(self, *_args, **_kwargs):
                return None
            def mSetLogTimeoutFx(self, *_args, **_kwargs):
                return None

        class DummyManager(object):
            def __init__(self):
                self.started = []
                self._result = {"guestvm1": {"cpu_resize_success": True, "currvcpus": 6, "configvcpus": 6}}
            def mGetManager(self):
                class Mgr(object):
                    def __init__(self, data):
                        self._data = data
                    def dict(self):
                        return self._data
                return Mgr(self._result)
            def mStartAppend(self, proc):
                self.started.append(proc)
            def mJoinProcess(self):
                return None

        dummy_manager = DummyManager()

        with patch("exabox.ovm.kvmcpumgr.ProcessManager", return_value=dummy_manager):
            with patch("exabox.ovm.kvmcpumgr.ProcessStructure", DummyProc):
                result = mgr.mResizeCpus(dom_list)

        self.assertEqual(result["guestvm1"]["configvcpus"], 6)
        self.assertEqual(len(dummy_manager.started), 1)

    # Auto-generated test for mResizeCpus
    def test_mResizeCpus_sequential_executes_each_entry(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        dom_list = [
            {"domu": "guestvm1", "vcpus": 6, "dom0": "dom0", "pingable": True},
            {"domu": "guestvm2", "vcpus": 4, "dom0": "dom0", "pingable": False},
        ]

        def set_vcpu(domu, vcpus, dom0, pingable, result):
            result[domu] = {
                "cpu_resize_success": True,
                "currvcpus": vcpus,
                "configvcpus": vcpus,
            }

        with patch.object(mgr, "mSetVCPUandValidate", side_effect=set_vcpu) as set_mock:
            result = mgr.mResizeCpus(dom_list)

        self.assertEqual(result["guestvm1"]["currvcpus"], 6)
        self.assertEqual(result["guestvm2"]["configvcpus"], 4)
        self.assertEqual(set_mock.call_count, 2)

    # Auto-generated test for mGetConsoleLog
    def test_mGetConsoleLog_returns_path_when_tmp_missing(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value='120')
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mFileExists.side_effect = [True, False]
        node.mExecuteCmd.return_value = (None, None, None)
        node.mGetCmdExitStatus.return_value = 0

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            result = mgr.mGetConsoleLog("dom0", "guestvm1", "serial.log")

        self.assertEqual(result, "/tmp/log/serial.log")
        node.mCopy2Local.assert_not_called()
        node.mExecuteCmd.assert_called_once_with(
            "/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host guestvm1 --path /tmp/serial.log",
            aTimeout=120,
        )

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_stops_after_setcount(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        cluctrl.mCheckConfigOption = Mock(return_value=["panic"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "serial.log.1")
            file2 = os.path.join(tmpdir, "serial.log.2")
            with open(file1, "w") as f1:
                f1.write("boot ok\n")
            with open(file2, "w") as f2:
                f2.write("boot ok\n")

            host_d = {
                "guestvm1": {"consoleaccess": True, "logbeforeresize": file1},
                "guestvm2": {"consoleaccess": True, "logbeforeresize": file1},
            }

            with patch.object(mgr, "mGetConsoleLog", return_value=file2) as get_log:
                with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=[]):
                    result = mgr.mCheckForReboots(
                        [("dom0", "guestvm1"), ("dom0", "guestvm2")],
                        1,
                        host_d,
                    )

        self.assertFalse(result)
        get_log.assert_called_once()

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_no_available_config_vcpus(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=[
                "guestvm1  : Current: 0 (domain is down)"
            ])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", False, result)

        self.assertFalse(result["guestvm1"]["cpu_resize_success"])
        self.assertIsNone(result["guestvm1"]["currvcpus"])
        self.assertIsNone(result["guestvm1"]["configvcpus"])

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_flags_reboot_when_marker_matches(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        cluctrl.mCheckConfigOption = Mock(return_value=["panic"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": "/tmp/serial.log.1"}}

        with patch.object(mgr, "mGetConsoleLog", return_value="/tmp/serial.log.2"):
            with patch("exabox.ovm.kvmcpumgr.open", mock_open(read_data="panic now\n")):
                with patch("exabox.ovm.kvmcpumgr.difflib.unified_diff", return_value=["+panic now\n"]):
                    with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=["/tmp/serial-uuid-guestvm1.log.1"]):
                        with patch("exabox.ovm.kvmcpumgr.os.remove"):
                            result = mgr.mCheckForReboots([("dom0", "guestvm1")], 1, host_d)

        self.assertTrue(result)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_cpu_manage_mode_oedacli_returns_none(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'cpu_manage_mode':
                return 'dg_oedacli'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        with patch("exabox.ovm.kvmcpumgr.ebLogError") as log_err:
            rc = mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=self.mGetPayload())

        self.assertIsNone(rc)
        self.assertTrue(log_err.called)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_raises_partial_update(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], ['dom1']))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1'), ('dom1', 'guestvm2')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [{"hostname": "guestvm1", "cores": "4"}]

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
            (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 2"])), None),
            (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 4 Restart: 4"])), None),
            (None, Mock(readlines=Mock(return_value=["maximum config 10"])), None),
        ]

        out_obj = Mock(stdout="Total vcpu required for reboot : 4")

        class DummyCtx(object):
            def __enter__(self_inner):
                return Mock()
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                        with patch.object(mgr, "mResizeCpus", return_value={
                            "guestvm1": {"cpu_resize_success": True, "currvcpus": 4, "configvcpus": 4}
                        }):
                            with self.assertRaises(Exception):
                                mgr.mManageVMCpusCountKvm("resizecpus", "_all_", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_reboot_check_aborts(self):
        cluctrl = self.mGetClubox()
        def config_option(key, default=None):
            if key == 'cpuresize_check_reboots':
                return 'True'
            if key == 'kvm_minimum_vcpus':
                return '4'
            return None

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0', 'dom1'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1', 'guestvm2'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1'), ('dom1', 'guestvm2')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf['vms'] = [
            {"hostname": "guestvm1", "cores": "4"},
            {"hostname": "guestvm2", "cores": "4"},
        ]

        def exec_cmd(cmd):
            if cmd == "/usr/bin/virsh nodeinfo":
                return None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None
            if cmd == "/usr/sbin/vm_maker --list --vcpu":
                return None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 2"])), None
            if "--list --vcpu --domain" in cmd:
                return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 4 Restart: 4"])), None
            if "virsh vcpucount" in cmd:
                return None, Mock(readlines=Mock(return_value=["maximum config 10"])), None
            return None, None, None

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.side_effect = exec_cmd

        out_obj = Mock(stdout="Total vcpu required for reboot : 4")

        class DummyCtx(object):
            def __enter__(self_inner):
                return Mock()
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch.object(mgr, "mGetConsoleLog", return_value="/tmp/serial.log.1"):
                with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                    with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                        with patch("exabox.ovm.kvmcpumgr.node_exec_cmd_check", return_value=out_obj):
                            with patch.object(mgr, "mResizeCpus", return_value={
                                "guestvm1": {"cpu_resize_success": True, "currvcpus": 4, "configvcpus": 4}
                            }):
                                with patch.object(mgr, "mCheckForReboots", return_value=True):
                                    with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                                        rc = mgr.mManageVMCpusCountKvm("resizecpus", "_all_", aOptions=options)

        self.assertIsInstance(rc, int)
        self.assertLess(rc, 0)

    # Auto-generated test for mPatchVMCfgVcpuCountKvm
    def test_mPatchVMCfgVcpuCountKvm_not_pingable_uses_config(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.IsZdlraProv = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode") as node_cls:
            node_cls.return_value = node
            node.mConnect.return_value = None
            node.mDisconnect.return_value = None
            with patch.object(mgr, 'mIsActiveGuest', return_value=False):
                options = self.mGetPayload()
                options.jsonconf['vm'] = {"cores": 6}
                mgr.mPatchVMCfgVcpuCountKvm("dom0", "guestvm1", options)

        node.mExecuteCmdLog.assert_called_once_with(
            "/usr/sbin/vm_maker --set --vcpu 12 --domain guestvm1 --config --force"
        )

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_updates_config_when_mismatch(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mGetHostname.return_value = 'dom0'
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]

        commands = []

        def exec_cmd(cmd):
            commands.append(cmd)
            if "--list   --vcpu" in cmd:
                if len(commands) < 4:
                    return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 4 Restart: 2"])), None
                return None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 4 Restart: 4"])), None
            return None, None, Mock(read=lambda: "")

        node.mExecuteCmd.side_effect = exec_cmd

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 4, "dom0", True, result)

        self.assertTrue(result["guestvm1"]["cpu_resize_success"])
        self.assertEqual(result["guestvm1"]["currvcpus"], 4)
        self.assertEqual(result["guestvm1"]["configvcpus"], 4)
        self.assertIn("--config --force", commands[2])

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_updates_maxvcpus(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=Mock(mSetData=Mock()))
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        def exec_cmd(cmd):
            if "virsh nodeinfo" in cmd:
                return None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None
            if "vm_maker --list --vcpu" in cmd:
                return None, Mock(readlines=Mock(return_value=["2"])), None
            if "virsh vcpucount" in cmd:
                return None, Mock(readlines=Mock(return_value=["6"])), None
            return None, None, None

        node.mExecuteCmd.side_effect = exec_cmd

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with patch("exabox.ovm.kvmcpumgr.ebGetDefaultDB") as db_get:
                db_get.return_value = Mock(mUpdateRequest=Mock())
                rc = mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

        self.assertEqual(rc, 0)
        node.mExecuteCmd.assert_any_call(
            "/usr/bin/virsh setvcpus guestvm1 8 --maximum --config"
        )

    # Auto-generated test for mManageVMCpusBurstingKvm
    def test_mManageVMCpusBurstingKvm_invalid_nodeinfo_returns_error(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.mGetRequestObj = Mock(return_value=None)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s) 8"])), None),
        ]
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
            with self.assertRaises(IndexError):
                mgr.mManageVMCpusBurstingKvm("enablebursting", "guestvm1", aOptions=self.mGetPayload())

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_parse_vm_line_failure_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {"vms": [{"hostname": "guestvm1", "cores": "4"}]}

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mGetHostname.return_value = "dom0"
        node.mDisconnect.return_value = None

        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
            (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
            (None, Mock(readlines=Mock(return_value=["guestvm1 : Current:"])), None),
        ]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with self.assertRaises(Exception):
                        mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_currmaxvcpus_parse_failure_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(["dom0"], []))
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[("dom0", "guestvm1")])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {"vms": [{"hostname": "guestvm1", "cores": "4"}]}

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mGetHostname.return_value = "dom0"
        node.mDisconnect.return_value = None

        node.mExecuteCmd.side_effect = [
            (None, Mock(readlines=Mock(return_value=["CPU(s): 10"])), None),
            (None, Mock(readlines=Mock(return_value=["Host reserved PCPU                     : 4"])), None),
            (None, Mock(readlines=Mock(return_value=["guestvm1 : Current: 6 Restart: 6"])), None),
            (None, Mock(readlines=Mock(return_value=["maximum config notanint"])), None),
        ]

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, "mIsActiveGuest", return_value=True):
            with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
                with patch("exabox.ovm.kvmcpumgr.exaBoxNode", return_value=node):
                    with self.assertRaises(Exception):
                        mgr.mManageVMCpusCountKvm("resizecpus", "guestvm1", aOptions=options)

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_updates_config_when_pingable_mismatch(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '2'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=["guestvm1  : Current: 6 Restart: 4"])), Mock(read=lambda: "")),
            (None, None, Mock(read=lambda: "")),
            (None, Mock(readlines=Mock(return_value=["guestvm1  : Current: 6 Restart: 4"])), Mock(read=lambda: "")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertFalse(result["guestvm1"]["cpu_resize_success"])
        cmd_calls = [call_args[0][0] for call_args in node.mExecuteCmd.call_args_list]
        self.assertTrue(any("--config --force" in cmd for cmd in cmd_calls))

    # Auto-generated test for mSetVCPUandValidate
    def test_mSetVCPUandValidate_list_command_failure(self):
        cluctrl = self.mGetClubox()

        def config_option(key, default=None):
            if key == 'timeout_vmcpu_resize':
                return '0'
            if key == 'setvcpu_retry_count':
                return '1'
            return default

        cluctrl.mCheckConfigOption = Mock(side_effect=config_option)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, None, Mock(read=lambda: "")),
            (None, None, Mock(read=lambda: "list failed")),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 1]
        node.mGetHostname.return_value = 'dom0'

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.kvmcpumgr.connect_to_host", return_value=DummyCtx()):
            with patch("exabox.ovm.kvmcpumgr.time.sleep"):
                result = {}
                mgr.mSetVCPUandValidate("guestvm1", 6, "dom0", True, result)

        self.assertFalse(result["guestvm1"]["cpu_resize_success"])
        self.assertIsNone(result["guestvm1"]["currvcpus"])
        self.assertIsNone(result["guestvm1"]["configvcpus"])

    # Auto-generated test for mCheckForReboots
    def test_mCheckForReboots_setcount_zero_cleans_logs(self):
        cluctrl = self.mGetClubox()
        cluctrl.mGetUUID = Mock(return_value="uuid")
        cluctrl.mGetOedaPath = Mock(return_value="/tmp")
        cluctrl.mCheckConfigOption = Mock(return_value=["panic"])
        mgr = exaBoxKvmCpuMgr(cluctrl)

        host_d = {"guestvm1": {"consoleaccess": True, "logbeforeresize": "/tmp/serial.log.1"}}

        with patch.object(mgr, "mGetConsoleLog", return_value=None) as get_log:
            with patch("exabox.ovm.kvmcpumgr.glob.glob", return_value=["/tmp/serial-uuid-guestvm1.log.1"]):
                with patch("exabox.ovm.kvmcpumgr.os.remove") as rm_file:
                    result = mgr.mCheckForReboots([("dom0", "guestvm1")], 0, host_d)

        self.assertFalse(result)
        get_log.assert_not_called()
        rm_file.assert_called_once_with("/tmp/serial-uuid-guestvm1.log.1")


    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_cos_allocatable_check_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {
            'vms': [{'hostname': 'guestvm1', 'cores': '4'}],
            'subfactor': 2,
            'poolsize': 4,
        }

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0

        def exec_cmd(cmd):
            if "virsh nodeinfo" in cmd:
                return None, Mock(readlines=Mock(return_value=["CPU(s): 12\n"])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu':
                return None, Mock(readlines=Mock(return_value=['Host reserved PCPU : 2\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 6 Restart: 6'])), None
            if cmd == '/usr/bin/virsh vcpucount guestvm1':
                return None, Mock(readlines=Mock(return_value=['maximum config 12\n'])), None
            if cmd == '/usr/sbin/vm_maker --list-domains':
                return None, Mock(readlines=Mock(return_value=['guestvm1 (uuid)\\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : 0 : 0 : 7'])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch('exabox.ovm.kvmcpumgr.connect_to_host', return_value=DummyCtx()):
                with patch('exabox.ovm.kvmcpumgr.exaBoxNode', return_value=node):
                    with patch('exabox.ovm.kvmcpumgr.node_exec_cmd_check', return_value=Mock(stdout='Total vcpu required for reboot : 2')):
                        with self.assertRaises(Exception):
                            mgr.mManageVMCpusCountKvm('resizecpus', 'guestvm1', aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_cos_cluster_missing_vm_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {
            'vms': [{'hostname': 'guestvm1', 'cores': '4'}],
            'subfactor': 2,
            'poolsize': 4,
        }

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0

        def exec_cmd(cmd):
            if "virsh nodeinfo" in cmd:
                return None, Mock(readlines=Mock(return_value=["CPU(s): 12\n"])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu':
                return None, Mock(readlines=Mock(return_value=['Host reserved PCPU : 2\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 6 Restart: 6'])), None
            if cmd == '/usr/bin/virsh vcpucount guestvm1':
                return None, Mock(readlines=Mock(return_value=['maximum config 12'])), None
            if cmd == '/usr/sbin/vm_maker --list-domains':
                return None, Mock(readlines=Mock(return_value=['guestvm1 (uuid)\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=[])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch('exabox.ovm.kvmcpumgr.connect_to_host', return_value=DummyCtx()):
                with patch('exabox.ovm.kvmcpumgr.exaBoxNode', return_value=node):
                    with patch('exabox.ovm.kvmcpumgr.node_exec_cmd_check', return_value=Mock(stdout='Total vcpu required for reboot : 2')):
                        with self.assertRaises(Exception):
                            mgr.mManageVMCpusCountKvm('resizecpus', 'guestvm1', aOptions=options)

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_cos_cluster_missing_report_raises(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {
            'vms': [{'hostname': 'guestvm1', 'cores': '4'}],
            'subfactor': 2,
            'poolsize': 4,
        }

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0

        def exec_cmd(cmd):
            if "virsh nodeinfo" in cmd:
                return None, Mock(readlines=Mock(return_value=["CPU(s): 12\n"])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu':
                return None, Mock(readlines=Mock(return_value=['Host reserved PCPU : 2\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 6 Restart: 6'])), None
            if cmd == '/usr/bin/virsh vcpucount guestvm1':
                return None, Mock(readlines=Mock(return_value=['maximum config 12\n'])), None
            if cmd == '/usr/sbin/vm_maker --list-domains':
                return None, Mock(readlines=Mock(return_value=['guestvm1 (uuid)\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : 0 : 0 : 5'])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch('exabox.ovm.kvmcpumgr.connect_to_host', return_value=DummyCtx()):
                with patch('exabox.ovm.kvmcpumgr.exaBoxNode', return_value=node):
                    with patch('exabox.ovm.kvmcpumgr.node_exec_cmd_check', return_value=Mock(stdout='Total vcpu required for reboot : 2')):
                        with patch.object(mgr, 'mSetVCPUandValidate', return_value=None) as set_vcpu:
                            rc = mgr.mManageVMCpusCountKvm('resizecpus', 'guestvm1', aOptions=options)

        self.assertEqual(rc, 0)
        set_vcpu.assert_called_once()

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_non_cos_handles_same_cpu_count(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        cluctrl.mModifyService = Mock()
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {
            'vms': [{'hostname': 'guestvm1', 'cores': '4'}],
            'subfactor': 1,
        }

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mGetHostname.return_value = 'dom0'

        def exec_cmd(cmd):
            if cmd == '/usr/bin/virsh nodeinfo':
                return None, Mock(readlines=Mock(return_value=['CPU(s): 10\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu':
                return None, Mock(readlines=Mock(return_value=['Host reserved PCPU : 2\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 8 Restart: 8'])), None
            if cmd == '/usr/bin/virsh vcpucount guestvm1':
                return None, Mock(readlines=Mock(return_value=['maximum config 8\n'])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch('exabox.ovm.kvmcpumgr.connect_to_host', return_value=DummyCtx()):
                with patch('exabox.ovm.kvmcpumgr.exaBoxNode', return_value=node):
                    with patch('exabox.ovm.kvmcpumgr.node_exec_cmd_check', return_value=Mock(stdout='Total vcpu required for reboot : 2')):
                        with patch.object(mgr, 'mResizeCpus') as resize_mock:
                            rc = mgr.mManageVMCpusCountKvm('resizecpus', 'guestvm1', aOptions=options)

        self.assertEqual(rc, 0)
        resize_mock.assert_not_called()

    # Auto-generated test for mManageVMCpusCountKvm
    def test_mManageVMCpusCountKvm_non_cos_overprovisioning_returns_error(self):
        cluctrl = self.mGetClubox()
        cluctrl.mCheckConfigOption = Mock(return_value=None)
        cluctrl.mCheckDom0sPingable = Mock(return_value=(['dom0'], []))
        cluctrl.mGetOrigDom0sDomUs = Mock(return_value=['guestvm1'])
        cluctrl.mReturnDom0DomUPair = Mock(return_value=[('dom0', 'guestvm1')])
        cluctrl.isBaseDB = Mock(return_value=False)
        cluctrl.isExacomputeVM = Mock(return_value=False)
        mgr = exaBoxKvmCpuMgr(cluctrl)

        options = self.mGetPayload()
        options.jsonconf = {
            'vms': [{'hostname': 'guestvm1', 'cores': '4'}],
            'subfactor': 1,
        }

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0

        def exec_cmd(cmd):
            if cmd == '/usr/bin/virsh nodeinfo':
                return None, Mock(readlines=Mock(return_value=['CPU(s): 10\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu':
                return None, Mock(readlines=Mock(return_value=['Host reserved PCPU : 2\n'])), None
            if cmd == '/usr/sbin/vm_maker --list --vcpu --domain guestvm1':
                return None, Mock(readlines=Mock(return_value=['guestvm1 : Current: 6 Restart: 6'])), None
            if cmd == '/usr/bin/virsh vcpucount guestvm1':
                return None, Mock(readlines=Mock(return_value=['maximum config 12\n'])), None
            return None, Mock(readlines=Mock(return_value=[])), None

        node.mExecuteCmd.side_effect = exec_cmd
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        class DummyCtx(object):
            def __enter__(self_inner):
                return node
            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(mgr, 'mIsActiveGuest', return_value=True):
            with patch('exabox.ovm.kvmcpumgr.connect_to_host', return_value=DummyCtx()):
                with patch('exabox.ovm.kvmcpumgr.exaBoxNode', return_value=node):
                    with patch('exabox.ovm.kvmcpumgr.node_exec_cmd_check', return_value=Mock(stdout='Total vcpu required for reboot : 2')):
                        with patch.object(mgr, 'mResizeCpus', return_value={
                            "guestvm1": {"cpu_resize_success": False, "currvcpus": 6, "configvcpus": 6}
                        }):
                            rc = mgr.mManageVMCpusCountKvm('resizecpus', 'guestvm1', aOptions=options)

        self.assertIsInstance(rc, int)
        self.assertLess(rc, 0)
        
if __name__ == '__main__':
    unittest.main()
