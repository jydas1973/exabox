#!/bin/python
#
# $Header: tests_handler_imagebase_copy_volumes.py 27-mar-2026.17:38:59 joysjose Exp $
#
# tests_handler_imagebase_copy_volumes.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_handler_imagebase_copy_volumes.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    04/10/26 - fix imagebase copy volume lock handling for unit
#                           tests
#    joysjose    03/27/26 - add unit tests for imagebase copy volumes handler
#    joysjose    03/27/26 - Creation
#
#!/bin/python
#
# tests_handler_imagebase_copy_volumes.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import json
import unittest

from unittest.mock import MagicMock, call, mock_open, patch

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_imagebase_copy_volumes import ImagebaseCopyVolume
from exabox.core.Error import ebError, ExacloudRuntimeError

class ebTestImagebaseCopyVolumes(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    @staticmethod
    def _ctx_manager(aNode):
        _ctx = MagicMock()
        _ctx.__enter__.return_value = aNode
        _ctx.__exit__.return_value = False
        return _ctx

    def test_mCreateNatDomUToClientDomUMapping_success(self):
        _handler = ImagebaseCopyVolume(self.mGetContext().mGetArgsOptions())

        with patch(
            "exabox.jsondispatch.handler_imagebase_copy_volumes.node_exec_cmd",
            side_effect=[
                (0, "nat-vm1.example.com.\nnat-vm2.example.com.\n", ""),
                (0, "client-vm1\nclient-vm2\n", ""),
            ],
        ):
            _mapping = _handler.mCreateNatDomUToClientDomUMapping(MagicMock())

        self.assertEqual(
            {
                "nat-vm1.example.com": "client-vm1",
                "nat-vm2.example.com": "client-vm2",
            },
            _mapping,
        )

    def test_mCreateNatDomUToClientDomUMapping_raises_on_mismatch(self):
        _handler = ImagebaseCopyVolume(self.mGetContext().mGetArgsOptions())

        with patch(
            "exabox.jsondispatch.handler_imagebase_copy_volumes.node_exec_cmd",
            side_effect=[
                (0, "nat-vm1.example.com.\n", ""),
                (0, "client-vm1\nclient-vm2\n", ""),
            ],
        ):
            with self.assertRaisesRegex(ValueError, "Mismatch between nat vms"):
                _handler.mCreateNatDomUToClientDomUMapping(MagicMock())

    def test_mExecute_builds_hostinfo_and_dispatches_volume_copies(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "image_base_bom": {
                "gold_image": {
                    "system_image": "/repo/system.img.bz2",
                    "u01_image": "/repo/u01.img.bz2",
                }
            },
            "customer_network": {
                "nodes": [
                    {
                        "volumes": [
                            {
                                "domU": "nat-vm1.example.com",
                                "attach_host": "dom0-host-a.example.com",
                                "dom0": "dom0-host-a.example.com",
                                "volumetype": "system",
                                "volumedevicepath": "/dev/exc/mapper/system001",
                            },
                            {
                                "attach_host": "dom0-host-a.example.com",
                                "dom0": "dom0-host-a.example.com",
                                "volumetype": "u01",
                                "volumedevicepath": "/dev/exc/mapper/u01001",
                            },
                        ]
                    },
                    {
                        "volumes": [
                            {
                                "domU": "nat-vm2.example.com",
                                "attach_host": "backup-host.example.com",
                                "dom0": "dom0-host-b.example.com",
                                "volumetype": "system",
                                "volumedevicepath": "/dev/exc/mapper/system002",
                            },
                            {
                                "attach_host": "backup-host.example.com",
                                "dom0": "dom0-host-b.example.com",
                                "volumetype": "u01",
                                "volumedevicepath": "/dev/exc/mapper/u01002",
                            },
                        ]
                    },
                ]
            },
        }

        _handler = ImagebaseCopyVolume(_options)
        _bom_spec = _options.jsonconf["image_base_bom"]

        with patch.object(_handler, "mCopyVolume") as aMockCopyVolume, \
             patch.object(ImagebaseCopyVolume, "mValidateDom0Host", return_value=None, create=True):
            self.assertEqual((0, {}), _handler.mExecute())

        self.assertEqual(
            [
                call(
                    _bom_spec,
                    {
                        "domU": "nat-vm1.example.com",
                        "dom0": "dom0-host-a.example.com",
                        "gold_system": "system001",
                        "gold_u01": "u01001",
                    },
                    "gold_system",
                ),
                call(
                    _bom_spec,
                    {
                        "domU": "nat-vm1.example.com",
                        "dom0": "dom0-host-a.example.com",
                        "gold_system": "system001",
                        "gold_u01": "u01001",
                    },
                    "gold_u01",
                ),
                call(
                    _bom_spec,
                    {
                        "domU": "nat-vm2.example.com",
                        "dom0": "dom0-host-b.example.com",
                        "gold_system": "system002",
                        "gold_u01": "u01002",
                    },
                    "gold_system",
                ),
                call(
                    _bom_spec,
                    {
                        "domU": "nat-vm2.example.com",
                        "dom0": "dom0-host-b.example.com",
                        "gold_system": "system002",
                        "gold_u01": "u01002",
                    },
                    "gold_u01",
                ),
            ],
            aMockCopyVolume.call_args_list,
        )

    def test_mExecute_without_image_base_bom_skips_copy(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {"customer_network": {"nodes": []}}

        _handler = ImagebaseCopyVolume(_options)

        with patch.object(_handler, "mCopyVolume") as aMockCopyVolume:
            self.assertEqual((0, {}), _handler.mExecute())

        aMockCopyVolume.assert_not_called()

    def test_mExecute_builds_hostinfo_from_later_volume_metadata(self):
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = {
            "image_base_bom": {
                "gold_image": {
                    "system_image": "/repo/system.img.bz2",
                    "u01_image": "/repo/u01.img.bz2",
                }
            },
            "customer_network": {
                "nodes": [
                    {
                        "volumes": [
                            {
                                "domU": "",
                                "attach_host": "dom0-host-a.example.com",
                                "dom0": "dom0-host-a.example.com",
                                "volumetype": "system",
                                "volumedevicepath": "/dev/exc/mapper/system001",
                            },
                            {
                                "domU": "nat-vm3.example.com",
                                "volumetype": "u01",
                                "volumedevicepath": "/dev/exc/mapper/u01003",
                            },
                        ]
                    }
                ]
            },
        }

        _handler = ImagebaseCopyVolume(_options)
        _bom_spec = _options.jsonconf["image_base_bom"]

        with patch.object(_handler, "mCopyVolume") as aMockCopyVolume, \
             patch.object(ImagebaseCopyVolume, "mValidateDom0Host", return_value=None, create=True):
            self.assertEqual((0, {}), _handler.mExecute())

        self.assertEqual(
            [
                call(
                    _bom_spec,
                    {
                        "domU": "nat-vm3.example.com",
                        "dom0": "dom0-host-a.example.com",
                        "gold_system": "system001",
                        "gold_u01": "u01003",
                    },
                    "gold_system",
                ),
                call(
                    _bom_spec,
                    {
                        "domU": "nat-vm3.example.com",
                        "dom0": "dom0-host-a.example.com",
                        "gold_system": "system001",
                        "gold_u01": "u01003",
                    },
                    "gold_u01",
                ),
            ],
            aMockCopyVolume.call_args_list,
        )

    def test_mCopyVolume_invalid_key_still_runs_cleanup(self):
        _handler = ImagebaseCopyVolume(self.mGetContext().mGetArgsOptions())
        _bom_spec = {
            "gold_image": {
                "system_image": "/repo/system.img.bz2",
                "u01_image": "/repo/u01.img.bz2",
            }
        }
        _host_info = {"dom0": "dom0-host", "domU": "domu-host"}
        _oss_open = mock_open(
            read_data=json.dumps({"bom_namespace": "ns", "bom_bucket": "bucket"})
        )
        _dom0_node = MagicMock()
        _domu_node = MagicMock()

        with patch("builtins.open", _oss_open), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.__file__", "/opt/unit/exacloud/exabox/jsondispatch/handler_imagebase_copy_volumes.py"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.uuid.uuid4", return_value="test-uuid"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.connect_to_host", side_effect=[
                 self._ctx_manager(_dom0_node),
                 self._ctx_manager(_domu_node),
             ]), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.node_exec_cmd_check") as aMockNodeCmdCheck, \
             patch.object(_handler, "mExecuteLocal") as aMockExecuteLocal:
            with self.assertRaisesRegex(ValueError, "Missing invalid_key in bom file"):
                _handler.mCopyVolume(_bom_spec, _host_info, "invalid_key")

        self.assertEqual(
            [
                call("/bin/mkdir -p /opt/unit/exacloud/tmp/test-uuid"),
                call("/bin/rm -rf /opt/unit/exacloud/tmp/test-uuid"),
            ],
            aMockExecuteLocal.call_args_list,
        )
        self.assertEqual(
            [
                call(_dom0_node, "/bin/rm -rf /opt/exacloud/test-uuid"),
                call(_domu_node, "/bin/rm -rf /opt/exacloud/test-uuid"),
            ],
            aMockNodeCmdCheck.call_args_list,
        )

    def test_mCopyVolume_failure_after_attach_still_detaches_and_cleans_up(self):
        _handler = ImagebaseCopyVolume(self.mGetContext().mGetArgsOptions())
        _bom_spec = {
            "gold_image": {
                "system_image": "/repo/system.img.bz2",
                "u01_image": "/repo/u01.img.bz2",
            }
        }
        _host_info = {
            "dom0": "dom0-host",
            "domU": "nat-vm1.example.com",
            "gold_system": "mapper-system",
        }
        _oss_open = mock_open(
            read_data=json.dumps({"bom_namespace": "ns", "bom_bucket": "bucket"})
        )
        _xml_open = mock_open()
        _dom0_node = MagicMock()
        _domu_node = MagicMock()
        _lock = MagicMock()

        def _open_side_effect(aPath, aMode="r", *args, **kwargs):
            if aPath == "exagip/config/oss.conf":
                return _oss_open(aPath, aMode, *args, **kwargs)
            return _xml_open(aPath, aMode, *args, **kwargs)

        def _node_exec_cmd_check(aNode, aCmd):
            if aCmd == "/bin/mkdir -p /opt/exacloud/test-uuid":
                return (0, "", "")
            if aCmd == "virsh attach-device client-vm1 /opt/exacloud/test-uuid/test-uuid.xml --live":
                return (0, "", "")
            if aCmd == "pbzip2 -t /opt/exacloud/test-uuid/system.img.bz2":
                raise RuntimeError("pbzip2 validation failed")
            return (0, "", "")

        with patch("builtins.open", side_effect=_open_side_effect), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.__file__", "/opt/unit/exacloud/exabox/jsondispatch/handler_imagebase_copy_volumes.py"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.uuid.uuid4", return_value="test-uuid"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.get_gcontext", return_value=object()), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.RemoteLock", return_value=_lock), \
             patch.object(_handler, "mGetUdevPath", side_effect=[None, "/dev/sdb"]), \
             patch.object(_handler, "mGetNextDeviceDom0", return_value="sdb"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.connect_to_host", side_effect=[
                 self._ctx_manager(_domu_node),
                 self._ctx_manager(_dom0_node),
                 self._ctx_manager(_domu_node),
                 self._ctx_manager(_dom0_node),
                 self._ctx_manager(_dom0_node),
                 self._ctx_manager(_domu_node),
             ]), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.node_exec_cmd_check", side_effect=_node_exec_cmd_check) as aMockNodeCmdCheck, \
             patch.object(_handler, "mCreateNatDomUToClientDomUMapping", return_value={"nat-vm1.example.com": "client-vm1"}), \
             patch.object(_handler, "mExecuteLocal") as aMockExecuteLocal:
            with self.assertRaisesRegex(RuntimeError, "pbzip2 validation failed"):
                _handler.mCopyVolume(_bom_spec, _host_info, "gold_system")

        self.assertEqual(
            [
                call("/bin/mkdir -p /opt/unit/exacloud/tmp/test-uuid"),
                call(
                    "/opt/unit/exacloud/bin/python "
                    "/opt/unit/exacloud/exagip/src/oss_instance_principal_script.py "
                    "download ns bucket --r1-cert=/opt/unit/exacloud/exabox/kms/combined_r1.crt "
                    "--from=/repo/system.img.bz2 --to=/opt/unit/exacloud/tmp/test-uuid/system.img.bz2"
                ),
                call("/bin/rm -rf /opt/unit/exacloud/tmp/test-uuid"),
            ],
            aMockExecuteLocal.call_args_list,
        )
        self.assertTrue(
            any(
                _call == call(
                    _dom0_node,
                    "virsh detach-disk client-vm1 /dev/exc/mapper-system --live",
                )
                for _call in aMockNodeCmdCheck.call_args_list
            )
        )
        self.assertEqual(
            [
                call(
                    "/opt/unit/exacloud/tmp/test-uuid/test-uuid.xml",
                    "/opt/exacloud/test-uuid/test-uuid.xml",
                )
            ],
            _dom0_node.mCopyFile.call_args_list,
        )
        self.assertEqual(
            [
                call(
                    "/opt/unit/exacloud/tmp/test-uuid/system.img.bz2",
                    "/opt/exacloud/test-uuid/system.img.bz2",
                )
            ],
            _domu_node.mCopyFile.call_args_list,
        )
        _lock.acquire.assert_called_once_with()
        _lock.release.assert_called_once_with()

    def test_mCopyVolume_lock_acquire_failure_skips_release_and_still_cleans_up(self):
        _handler = ImagebaseCopyVolume(self.mGetContext().mGetArgsOptions())
        _bom_spec = {
            "gold_image": {
                "system_image": "/repo/system.img.bz2",
                "u01_image": "/repo/u01.img.bz2",
            }
        }
        _host_info = {
            "dom0": "dom0-host",
            "domU": "nat-vm1.example.com",
            "gold_system": "mapper-system",
        }
        _lock = MagicMock()
        _lock.acquire.side_effect = ValueError('Unable to obtain the "agent_port" from ')
        _oss_open = mock_open(
            read_data=json.dumps({"bom_namespace": "ns", "bom_bucket": "bucket"})
        )
        _dom0_node = MagicMock()
        _domu_node = MagicMock()

        with patch("builtins.open", _oss_open), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.__file__", "/opt/unit/exacloud/exabox/jsondispatch/handler_imagebase_copy_volumes.py"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.uuid.uuid4", return_value="test-uuid"), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.RemoteLock", return_value=_lock), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.connect_to_host", side_effect=[
                 self._ctx_manager(_dom0_node),
                 self._ctx_manager(_domu_node),
             ]), \
             patch("exabox.jsondispatch.handler_imagebase_copy_volumes.node_exec_cmd_check") as aMockNodeCmdCheck, \
             patch.object(_handler, "mExecuteLocal") as aMockExecuteLocal:
            with self.assertRaisesRegex(ValueError, 'Unable to obtain the "agent_port"'):
                _handler.mCopyVolume(_bom_spec, _host_info, "gold_system")

        self.assertEqual(
            [
                call("/bin/mkdir -p /opt/unit/exacloud/tmp/test-uuid"),
                call(
                    "/opt/unit/exacloud/bin/python "
                    "/opt/unit/exacloud/exagip/src/oss_instance_principal_script.py "
                    "download ns bucket --r1-cert=/opt/unit/exacloud/exabox/kms/combined_r1.crt "
                    "--from=/repo/system.img.bz2 --to=/opt/unit/exacloud/tmp/test-uuid/system.img.bz2"
                ),
                call("/bin/rm -rf /opt/unit/exacloud/tmp/test-uuid"),
            ],
            aMockExecuteLocal.call_args_list,
        )
        self.assertEqual(
            [
                call(_dom0_node, "/bin/rm -rf /opt/exacloud/test-uuid"),
                call(_domu_node, "/bin/rm -rf /opt/exacloud/test-uuid"),
            ],
            aMockNodeCmdCheck.call_args_list,
        )
        _lock.acquire.assert_called_once_with()
        _lock.release.assert_not_called()

    def test_mCopyVolume_success_for_gold_system_and_gold_u01(self):
        _bom_spec = {
            "gold_image": {
                "system_image": "/repo/system.img.bz2",
                "u01_image": "/repo/u01.img.bz2",
            }
        }

        for _key, _volume_name, _disk_name, _unit in [
            ("gold_system", "mapper-system", "system.img.bz2", "1"),
            ("gold_u01", "mapper-u01", "u01.img.bz2", "1"),
        ]:
            with self.subTest(key=_key):
                _handler = ImagebaseCopyVolume(self.mGetContext().mGetArgsOptions())
                _lock = MagicMock()
                _host_info = {
                    "dom0": "dom0-host",
                    "domU": "nat-vm1.example.com",
                    _key: _volume_name,
                }
                _dom0_node = MagicMock()
                _domu_node = MagicMock()
                _oss_open = mock_open(
                    read_data=json.dumps({"bom_namespace": "ns", "bom_bucket": "bucket"})
                )
                _xml_open = mock_open()

                def _open_side_effect(aPath, aMode="r", *args, **kwargs):
                    if aPath == "exagip/config/oss.conf":
                        return _oss_open(aPath, aMode, *args, **kwargs)
                    return _xml_open(aPath, aMode, *args, **kwargs)

                def _node_exec_cmd_check(aNode, aCmd):
                    if aCmd.startswith('dmesg | grep "Attached SCSI disk"'):
                        return (0, f"[100.00] sd 0:0:7:{_unit}: [sdb] Attached SCSI disk\n", "")
                    if "parted ---pretend-input-tty /dev/sdb print" in aCmd:
                        return (0, "Partition table fixed", "")
                    return (0, "", "")

                with patch("builtins.open", side_effect=_open_side_effect), \
                     patch("exabox.jsondispatch.handler_imagebase_copy_volumes.__file__", "/opt/unit/exacloud/exabox/jsondispatch/handler_imagebase_copy_volumes.py"), \
                     patch("exabox.jsondispatch.handler_imagebase_copy_volumes.uuid.uuid4", return_value="test-uuid"), \
                     patch("exabox.jsondispatch.handler_imagebase_copy_volumes.get_gcontext", return_value=object()), \
                     patch("exabox.jsondispatch.handler_imagebase_copy_volumes.RemoteLock", return_value=_lock), \
                     patch.object(_handler, "mGetUdevPath", side_effect=[None, "/dev/sdb"]), \
                     patch.object(_handler, "mGetNextDeviceDom0", return_value="sdb"), \
                     patch("exabox.jsondispatch.handler_imagebase_copy_volumes.connect_to_host", side_effect=[
                         self._ctx_manager(_domu_node),
                         self._ctx_manager(_dom0_node),
                         self._ctx_manager(_domu_node),
                         self._ctx_manager(_dom0_node),
                         self._ctx_manager(_dom0_node),
                         self._ctx_manager(_domu_node),
                     ]) as aMockConnectToHost, \
                     patch("exabox.jsondispatch.handler_imagebase_copy_volumes.node_exec_cmd_check", side_effect=_node_exec_cmd_check) as aMockNodeCmdCheck, \
                     patch.object(_handler, "mCreateNatDomUToClientDomUMapping", return_value={"nat-vm1.example.com": "client-vm1"}), \
                     patch.object(_handler, "mExecuteLocal") as aMockExecuteLocal:
                    _handler.mCopyVolume(_bom_spec, _host_info, _key)

                self.assertEqual(
                    [
                        call("/bin/mkdir -p /opt/unit/exacloud/tmp/test-uuid"),
                        call(
                            "/opt/unit/exacloud/bin/python "
                            "/opt/unit/exacloud/exagip/src/oss_instance_principal_script.py "
                            "download ns bucket --r1-cert=/opt/unit/exacloud/exabox/kms/combined_r1.crt "
                            f"--from=/repo/{_disk_name} --to=/opt/unit/exacloud/tmp/test-uuid/{_disk_name}"
                        ),
                        call("/bin/rm -rf /opt/unit/exacloud/tmp/test-uuid"),
                    ],
                    aMockExecuteLocal.call_args_list,
                )
                _xml_open().write.assert_called_once()
                self.assertIn(f"/dev/exc/{_volume_name}", _xml_open().write.call_args[0][0])
                self.assertIn(f"unit='{_unit}'", _xml_open().write.call_args[0][0])
                _dom0_node.mCopyFile.assert_called_once_with(
                    "/opt/unit/exacloud/tmp/test-uuid/test-uuid.xml",
                    "/opt/exacloud/test-uuid/test-uuid.xml",
                )
                _domu_node.mCopyFile.assert_called_once_with(
                    f"/opt/unit/exacloud/tmp/test-uuid/{_disk_name}",
                    f"/opt/exacloud/test-uuid/{_disk_name}",
                )
                self.assertEqual(6, aMockConnectToHost.call_count)
                self.assertTrue(
                    any(
                        "virsh attach-device client-vm1 /opt/exacloud/test-uuid/test-uuid.xml --live"
                        == _call.args[1]
                        for _call in aMockNodeCmdCheck.call_args_list
                    )
                )
                self.assertTrue(
                    any(
                        f"pbzip2 -dc /opt/exacloud/test-uuid/{_disk_name} | dd of=/dev/sdb bs=64K"
                        == _call.args[1]
                        for _call in aMockNodeCmdCheck.call_args_list
                    )
                )
                self.assertTrue(
                    any(
                        f"virsh detach-disk client-vm1 /dev/exc/{_volume_name} --live"
                        == _call.args[1]
                        for _call in aMockNodeCmdCheck.call_args_list
                    )
                )
                _lock.acquire.assert_called_once_with()
                _lock.release.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
