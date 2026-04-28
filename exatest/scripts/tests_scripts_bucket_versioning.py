#!/usr/bin/env python3
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import argparse
import importlib.util
import os
import sys
import types
import unittest
from unittest import mock

try:
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
except ImportError:
    class ebTestClucontrol(unittest.TestCase):
        pass


VIEW_ROOT = os.environ.get("ADE_VIEW_ROOT", "/ade/joysjose_voxioissue2")
SCRIPTS_ROOT = os.path.join(VIEW_ROOT, "ecs", "exacloud", "scripts")
BUCKET_VERSIONING_PATH = os.path.join(SCRIPTS_ROOT, "bucket_versioning.py")


def _load_module(module_name, module_path, injected_modules=None):
    added_modules = []
    try:
        for name, module in (injected_modules or {}).items():
            if name not in sys.modules:
                added_modules.append(name)
            sys.modules[name] = module

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name in added_modules:
            sys.modules.pop(name, None)


def _build_bucket_versioning_stubs():
    stubs = {}

    oci_module = types.ModuleType("oci")
    exceptions_module = types.ModuleType("oci.exceptions")
    identity_module = types.ModuleType("oci.identity")
    identity_models_module = types.ModuleType("oci.identity.models")
    object_storage_module = types.ModuleType("oci.object_storage")
    object_storage_models_module = types.ModuleType("oci.object_storage.models")
    response_module = types.ModuleType("oci.response")
    retry_module = types.ModuleType("oci.retry")

    class ServiceError(Exception):
        pass

    class IdentityClient(object):
        pass

    class Compartment(object):
        pass

    class ObjectStorageClient(object):
        pass

    class Bucket(object):
        VERSIONING_ENABLED = "Enabled"
        VERSIONING_SUSPENDED = "Suspended"

        def __init__(self, name=None, namespace=None, versioning=None):
            self.name = name
            self.namespace = namespace
            self.versioning = versioning

    class UpdateBucketDetails(object):
        def __init__(self, versioning=None):
            self.versioning = versioning

    class Response(object):
        def __init__(self, status=None, data=None):
            self.status = status
            self.data = data

    exceptions_module.ServiceError = ServiceError
    identity_module.IdentityClient = IdentityClient
    identity_models_module.Compartment = Compartment
    object_storage_module.ObjectStorageClient = ObjectStorageClient
    object_storage_models_module.Bucket = Bucket
    object_storage_models_module.UpdateBucketDetails = UpdateBucketDetails
    response_module.Response = Response
    retry_module.DEFAULT_RETRY_STRATEGY = object()

    exabox_module = types.ModuleType("exabox")
    exaoci_module = types.ModuleType("exabox.exaoci")
    factory_module = types.ModuleType("exabox.exaoci.ExaOCIFactory")
    connectors_module = types.ModuleType("exabox.exaoci.connectors")
    config_connector_module = types.ModuleType("exabox.exaoci.connectors.ConfigFileConnector")
    r1_connector_module = types.ModuleType("exabox.exaoci.connectors.R1Connector")
    exabox_conf_connector_module = types.ModuleType("exabox.exaoci.connectors.ExaboxConfConnector")
    region_connector_module = types.ModuleType("exabox.exaoci.connectors.RegionConnector")

    class ExaOCIFactory(object):
        pass

    class ConfigFileConnector(object):
        pass

    class R1Connector(object):
        pass

    class ExaboxConfConnector(object):
        pass

    class RegionConnector(object):
        pass

    factory_module.ExaOCIFactory = ExaOCIFactory
    config_connector_module.ConfigFileConnector = ConfigFileConnector
    r1_connector_module.R1Connector = R1Connector
    exabox_conf_connector_module.ExaboxConfConnector = ExaboxConfConnector
    region_connector_module.RegionConnector = RegionConnector

    stubs["oci"] = oci_module
    stubs["oci.exceptions"] = exceptions_module
    stubs["oci.identity"] = identity_module
    stubs["oci.identity.models"] = identity_models_module
    stubs["oci.object_storage"] = object_storage_module
    stubs["oci.object_storage.models"] = object_storage_models_module
    stubs["oci.response"] = response_module
    stubs["oci.retry"] = retry_module
    stubs["exabox"] = exabox_module
    stubs["exabox.exaoci"] = exaoci_module
    stubs["exabox.exaoci.ExaOCIFactory"] = factory_module
    stubs["exabox.exaoci.connectors"] = connectors_module
    stubs["exabox.exaoci.connectors.ConfigFileConnector"] = config_connector_module
    stubs["exabox.exaoci.connectors.R1Connector"] = r1_connector_module
    stubs["exabox.exaoci.connectors.ExaboxConfConnector"] = exabox_conf_connector_module
    stubs["exabox.exaoci.connectors.RegionConnector"] = region_connector_module
    return stubs


class ebTestScriptsBucketVersioning(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        pass

    def _load_module(self):
        return _load_module(
            "bucket_versioning_test",
            BUCKET_VERSIONING_PATH,
            injected_modules=_build_bucket_versioning_stubs()
        )

    def test_mrun_exits_when_tenancy_details_are_missing(self):
        module = self._load_module()
        fake_oss_client = mock.Mock()
        fake_oss_client.get_namespace.return_value = types.SimpleNamespace(data="namespace")
        fake_factory = mock.Mock()
        fake_factory.get_object_storage_client.return_value = fake_oss_client
        fake_factory.get_identity_client.return_value = mock.Mock()

        args = argparse.Namespace(
            list=False,
            enable=False,
            disable=False,
            tenancy_ocid=None,
            compartment_name=None,
            bucket_name=None
        )

        with mock.patch.object(module, "ExaOCIFactory", return_value=fake_factory), \
             mock.patch.object(module, "mGetTenancyDetails", return_value=None), \
             mock.patch.object(module, "mLog") as log_mock:
            with self.assertRaises(SystemExit) as ctx:
                module.mRun(args)

        self.assertEqual(ctx.exception.code, 1)
        log_mock.assert_any_call("Could not retrieve tenancy details. Exiting.")

    def test_mrun_lists_buckets_for_named_compartment(self):
        module = self._load_module()
        bucket = types.SimpleNamespace(name="bucket-a", versioning="Disabled")
        root_compartment = types.SimpleNamespace(name="vmboss_compartment", id="root-id")
        child_compartment = types.SimpleNamespace(name="child-compartment", id="child-id")

        fake_oss_client = mock.Mock()
        fake_oss_client.get_namespace.return_value = types.SimpleNamespace(data="namespace")
        fake_identity_client = mock.Mock()
        fake_factory = mock.Mock()
        fake_factory.get_object_storage_client.return_value = fake_oss_client
        fake_factory.get_identity_client.return_value = fake_identity_client

        args = argparse.Namespace(
            list=True,
            enable=False,
            disable=False,
            tenancy_ocid="tenant-id",
            compartment_name="child-compartment",
            bucket_name=None
        )

        with mock.patch.object(module, "ExaOCIFactory", return_value=fake_factory), \
             mock.patch.object(module, "mGetCompartment", side_effect=[root_compartment, child_compartment]), \
             mock.patch.object(module, "mGetCompartments", return_value=[]), \
             mock.patch.object(module, "mGetBuckets", return_value=[bucket]) as get_buckets_mock, \
             mock.patch.object(module, "mPrintAsTable") as print_table_mock, \
             mock.patch.object(module, "mLog"):
            with self.assertRaises(SystemExit) as ctx:
                module.mRun(args)

        self.assertEqual(ctx.exception.code, 0)
        get_buckets_mock.assert_called_once_with(fake_oss_client, "namespace", "child-id")
        print_table_mock.assert_called_once_with([
            {"Bucket Name": "bucket-a", "Versioning State": "Disabled"}
        ])

    def test_mrun_updates_named_compartment_buckets(self):
        module = self._load_module()
        bucket = types.SimpleNamespace(name="bucket-a", versioning="Disabled")
        root_compartment = types.SimpleNamespace(name="vmboss_compartment", id="root-id")
        child_compartment = types.SimpleNamespace(name="child-compartment", id="child-id")

        fake_oss_client = mock.Mock()
        fake_oss_client.get_namespace.return_value = types.SimpleNamespace(data="namespace")
        fake_identity_client = mock.Mock()
        fake_factory = mock.Mock()
        fake_factory.get_object_storage_client.return_value = fake_oss_client
        fake_factory.get_identity_client.return_value = fake_identity_client

        args = argparse.Namespace(
            list=False,
            enable=True,
            disable=False,
            tenancy_ocid="tenant-id",
            compartment_name="child-compartment",
            bucket_name=None
        )

        with mock.patch.object(module, "ExaOCIFactory", return_value=fake_factory), \
             mock.patch.object(module, "mGetCompartment", side_effect=[root_compartment, child_compartment]), \
             mock.patch.object(module, "mGetCompartments", return_value=[]), \
             mock.patch.object(module, "mGetBuckets", return_value=[bucket]) as get_buckets_mock, \
             mock.patch.object(module, "mUpdateBucketVersioning") as update_mock, \
             mock.patch.object(module, "mLog"):
            with self.assertRaises(SystemExit) as ctx:
                module.mRun(args)

        self.assertEqual(ctx.exception.code, 0)
        get_buckets_mock.assert_called_once_with(fake_oss_client, "namespace", "child-id")
        update_mock.assert_called_once_with(fake_oss_client, bucket, "Enabled")


if __name__ == "__main__":
    unittest.main()
