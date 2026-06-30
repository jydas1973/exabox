#!/bin/python
#
# $Header$
#
# tests_exadata_bundles_purge.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_exadata_bundles_purge.py - Unit tests for exadata bundle purge
#
#    DESCRIPTION
#      Unit tests for exadata_bundles_purge.py virtualization-specific system
#      image cleanup.
#
#    NOTES
#      No
#
#    MODIFIED   (MM/DD/YY)
#    remamid     06/18/26 - Bug 39575767 add ExaTest coverage for UEFI purge
#
import unittest
from unittest.mock import MagicMock, patch

from exabox.infrapatching.utils import exadata_bundles_purge


class _FakeExadataVersionConfig:
    def __init__(self, config_file):
        self.config_file = config_file

    def load_file(self):
        return True

    def search_common_infra(self, _version):
        return {"retain": True}

    def search_common_compute(self, _version):
        return {"retain": True}

    def search_exasplice(self, _version):
        return {"retain": True}

    def search_system_image(self, _version):
        return True

    def search_cpsos(self, _version):
        return {"retain": True}

    def remove_exadata_tarballs(self, _exadata_folder):
        return None

    def remove_exasplice_tarballs(self, _exadata_folder):
        return None

    def metadata_file_sync(self, _metadata_file):
        return None


class _FakeMetadataFileSync:
    def __init__(self, _patch_download, _input_json_name):
        pass

    def mSyncPatchCommonJson(self):
        return None

    def mRemovePurgedCommmonJson(self):
        return None


class ebTestExadataBundlesPurge(unittest.TestCase):
    EXADATA_FOLDER = "/u01/downloads/exadata"
    IMAGES_FOLDER = f"{EXADATA_FOLDER}/images"
    PATCH_PAYLOADS_FOLDER = f"{EXADATA_FOLDER}/PatchPayloads"

    IMAGE_FILES = [
        "System.first.boot.25.1.18.0.0.260604.1.uefi.img.bz2",
        "System.first.boot.25.1.18.0.0.260604.1.kvm.img.bz2",
        "System.first.boot.25.1.18.0.0.260604.1.rtg.img.bz2",
        "System.first.boot.25.1.18.0.0.260604.1.img.bz2",
    ]

    def _exists(self, path):
        return path in (self.EXADATA_FOLDER, self.IMAGES_FOLDER, self.PATCH_PAYLOADS_FOLDER)

    def _isdir(self, path):
        return self._exists(path)

    def _listdir(self, path):
        if path == self.IMAGES_FOLDER:
            return list(self.IMAGE_FILES)
        return []

    def _run_purge(self, virtualization_type):
        with patch.object(exadata_bundles_purge.getpass, "getuser", return_value="ecra"), \
             patch.object(exadata_bundles_purge, "PurgeLog", return_value=MagicMock()), \
             patch.object(exadata_bundles_purge, "ExadataVersionConfig", _FakeExadataVersionConfig), \
             patch.object(exadata_bundles_purge, "MetadataFileSync", _FakeMetadataFileSync), \
             patch.object(exadata_bundles_purge, "active_process", return_value=False), \
             patch.object(exadata_bundles_purge, "virtualization_type", return_value=virtualization_type), \
             patch.object(exadata_bundles_purge, "mPurgeExtractedExadataVersion"), \
             patch.object(exadata_bundles_purge.os.path, "exists", side_effect=self._exists), \
             patch.object(exadata_bundles_purge.os.path, "isdir", side_effect=self._isdir), \
             patch.object(exadata_bundles_purge.os, "listdir", side_effect=self._listdir), \
             patch.object(exadata_bundles_purge, "remove_system_image") as remove_system_image:
            exadata_bundles_purge.main()
            return [call_args[0][1] for call_args in remove_system_image.call_args_list]

    def test_xen_purges_uefi_kvm_and_rtg_images(self):
        removed_images = self._run_purge(exadata_bundles_purge.virtualization_xen)

        self.assertCountEqual(
            [
                "System.first.boot.25.1.18.0.0.260604.1.uefi.img.bz2",
                "System.first.boot.25.1.18.0.0.260604.1.kvm.img.bz2",
                "System.first.boot.25.1.18.0.0.260604.1.rtg.img.bz2",
            ],
            removed_images,
        )

    def test_kvm_keeps_kvm_and_rtg_images(self):
        removed_images = self._run_purge(exadata_bundles_purge.virtualization_kvm)

        self.assertCountEqual(
            [
                "System.first.boot.25.1.18.0.0.260604.1.uefi.img.bz2",
                "System.first.boot.25.1.18.0.0.260604.1.img.bz2",
            ],
            removed_images,
        )


if __name__ == "__main__":
    unittest.main()
