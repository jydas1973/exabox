#!/bin/python
#
# $Header: tests_exakmssiv.py 26-feb-2026.09:05:54 prsshukl Exp $
#
# tests_exakmssiv.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmssiv.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    02/26/26 - Creation
#

import base64
import json
import unittest
from unittest import mock

import oci

from exabox.core.Error import ExacloudRuntimeError
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.exakms.ExaKmsEntrySIV import ExaKmsEntrySIVRSA, ExaKmsEntrySIVECDSA
from exabox.exakms.ExaKmsSIV import ExaKmsSIV
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class DummyHistory:
    def __init__(self):
        self.calls = []

    def mPutExaKmsHistory(self, entry, operation):
        self.calls.append((entry, operation))


class DummyResponse:
    def __init__(self, data, has_next_page=False, next_page=None):
        self.data = data
        self.has_next_page = has_next_page
        self.next_page = next_page


class DummyVault:
    def __init__(self, secrets=None, versions=None, update_error=None,
                 schedule_error=None):
        self._secrets = secrets or []
        self._versions = versions or []
        self._update_error = update_error
        self._schedule_error = schedule_error
        self.update_calls = []
        self.scheduled = []

    def list_secrets(self, page=None, vault_id=None, compartment_id=None):
        return DummyResponse(self._secrets, False, None)

    def list_secret_versions(self, secret_id, page=None):
        return DummyResponse(self._versions, False, None)

    def update_secret(self, secret_id=None, update_secret_details=None):
        self.update_calls.append((secret_id, update_secret_details))
        if self._update_error:
            raise self._update_error

    def create_secret(self, create_secret_details=None):
        self.update_calls.append(("create", create_secret_details))

    def schedule_secret_version_deletion(self, secret_id, version_number,
                                         version_details):
        if self._schedule_error:
            raise self._schedule_error
        self.scheduled.append((secret_id, version_number, version_details))


class DummySecretsClient:
    def __init__(self, bundle=None, bundle_error=None):
        self.bundle = bundle
        self.bundle_error = bundle_error
        self.calls = []

    def get_secret_bundle_by_name(self, name, vault_id):
        self.calls.append((name, vault_id))
        if self.bundle_error:
            raise self.bundle_error
        return mock.Mock(data=self.bundle)


class DummySecretBundleContent:
    def __init__(self, content):
        self.content = content


class DummySecretBundle:
    def __init__(self, content, secret_id="secret-1"):
        self.secret_bundle_content = DummySecretBundleContent(content)
        self.secret_id = secret_id
        self.id = secret_id

    def __repr__(self):
        return "<DummySecretBundle>"


class DummySecretSummary:
    def __init__(self, secret_name, secret_id="secret-id"):
        self.secret_name = secret_name
        self.id = secret_id
        self.secret_id = secret_id

    def __repr__(self):
        return "<DummySecretSummary>"



class DummyVaultComposite:
    def __init__(self, vault):
        self.vault = vault
        self.calls = []

    def create_secret_and_wait_for_state(self, create_secret_details=None,
                                         wait_for_states=None):
        self.calls.append((create_secret_details, wait_for_states))


class DummyContext:
    def __init__(self, options):
        self._options = dict(options)

    def mCheckConfigOption(self, key):
        return self._options.get(key)


class DummyRegContext(DummyContext):
    def __init__(self, options):
        super().__init__(options)
        self._registry = {}

    def mSetRegEntry(self, key, value):
        self._registry[key] = value

    def mCheckRegEntry(self, key):
        return key in self._registry

    def mDelRegEntry(self, key):
        if key in self._registry:
            del self._registry[key]


class DummySecretVersion:
    def __init__(self, secret_id, version_number, stages, time_of_deletion=None):
        self.secret_id = secret_id
        self.version_number = version_number
        self.stages = stages
        self.time_of_deletion = time_of_deletion


def _make_secret_content(data):
    payload = json.dumps(data).encode("utf-8")
    return base64.b64encode(payload).decode("utf-8")


class ebTestExaKmsSIV(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestExaKmsSIV, cls).setUpClass()

    def setUp(self):
        super().setUp()
        def _safe_set_enc_data(entry_self, enc_data):
            entry_self._ExaKmsEntrySIV__encData = enc_data
        self.context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": "backup-key",
        })

        self.factory = mock.Mock()
        self.vault = DummyVault()
        self.secrets_client = DummySecretsClient()
        self.factory.get_vault_client.return_value = self.vault
        self.factory.get_secrets_client.return_value = self.secrets_client

        self.gcontext_patch = mock.patch(
            "exabox.exakms.ExaKmsSIV.get_gcontext",
            return_value=self.context)
        self.factory_patch = mock.patch(
            "exabox.exakms.ExaKmsSIV.ExaOCIFactory",
            return_value=self.factory)
        self.history_patch = mock.patch(
            "exabox.exakms.ExaKmsSIV.ExaKmsHistorySIV",
            side_effect=lambda _: DummyHistory())
        self.vault_comp_patch = mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations",
            side_effect=lambda vault: DummyVaultComposite(vault))
        self.enc_data_patch = mock.patch(
            "exabox.exakms.ExaKmsEntrySIV.ExaKmsEntrySIV.mSetEncData",
            new=_safe_set_enc_data)

        self.gcontext_patch.start()
        self.factory_patch.start()
        self.history_patch.start()
        self.vault_comp_patch.start()
        self.enc_data_patch.start()

        self.addCleanup(self.gcontext_patch.stop)
        self.addCleanup(self.factory_patch.stop)
        self.addCleanup(self.history_patch.stop)
        self.addCleanup(self.vault_comp_patch.stop)
        self.addCleanup(self.enc_data_patch.stop)

    def _build_exakms(self):
        return ExaKmsSIV()

    def _build_exakms_with_context(self, context):
        self.gcontext_patch.stop()
        self.gcontext_patch = mock.patch(
            "exabox.exakms.ExaKmsSIV.get_gcontext",
            return_value=context)
        self.gcontext_patch.start()
        self.addCleanup(self.gcontext_patch.stop)
        return ExaKmsSIV()

    def _create_entry(self, fqdn="host1.exa", user="opc"):
        entry = ExaKmsEntrySIVRSA(fqdn, user, "")
        entry.mSetKeyId("key-id")
        entry.mSetEncData("enc-data")
        entry.mSetSecretName(fqdn)
        entry.mSetHostType(ExaKmsHostType.DOM0)
        entry.mSetLabel("label")
        entry.mSetExacloudHost("exa-host")
        entry.mSetKeyValueInfo({"k": "v"})
        entry.mSetHash("hash")
        entry.mSetCreationTime("2024-01-01 00:00:00")
        return entry

    def test_search_entries_from_cache(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        entry = self._create_entry()
        exakms.mSetCache({entry.mGetFQDN(): entry})

        with mock.patch.object(exakms, "mFilterCache", return_value=[entry]) as mfilter:
            result = exakms.mSearchExaKmsEntries({"FQDN": entry.mGetFQDN()})

        self.assertEqual(result, [entry])
        mfilter.assert_called_once()

    def test_search_entries_with_not_found_secret(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        error = oci.exceptions.ServiceError(404, "NotAuthorizedOrNotFound",
                                            {}, "not found")
        self.secrets_client.bundle_error = error

        result = exakms.mSearchExaKmsEntries({"FQDN": "host1.exa"}, aRefreshKey=True)

        self.assertEqual(result, [])

    def test_search_entries_with_non_404_error(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        error = oci.exceptions.ServiceError(500, "InternalError",
                                            {}, "boom")
        self.secrets_client.bundle_error = error

        with self.assertRaises(oci.exceptions.ServiceError):
            exakms.mSearchExaKmsEntries({"FQDN": "host1"}, aRefreshKey=True)

    def test_search_entries_with_dot_secret_name(self):
        # Auto-generated test for mSearchExaKmsEntries
        secret_data = {
            "id_rsa.host2.user1": {
                "keyId": "k1",
                "encData": "e1",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))
        self.secrets_client.bundle = bundle
        exakms = self._build_exakms()

        entries = exakms.mSearchExaKmsEntries({"FQDN": "host1.exa"},
                                              aRefreshKey=True)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].mGetFQDN(), "host1.exa")

    def test_search_entries_with_user_filter(self):
        # Auto-generated test for mSearchExaKmsEntries
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
                "version": "RSA",
            },
            "id_rsa.host1.user2": {
                "keyId": "k2",
                "encData": "e2",
                "version": "ECDSA",
            },
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))
        self.secrets_client.bundle = bundle
        exakms = self._build_exakms()

        entries = exakms.mSearchExaKmsEntries({"FQDN": "host1", "user": "user2"},
                                              aRefreshKey=True)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].mGetUser(), "user2")

    def test_list_secrets_backup_vault(self):
        # Auto-generated test for mListSecrets
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("s1"), DummySecretSummary("s2")]

        secrets = exakms.mListSecrets(aBackupVault=True)

        self.assertEqual([s.secret_name for s in secrets], ["s1", "s2"])

    def test_search_entries_refreshes_cache(self):
        # Auto-generated test for mSearchExaKmsEntries
        secret_data = {
            "id_rsa.host1.user1": {"keyId": "k1", "encData": "e1"}
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))
        self.secrets_client.bundle = bundle
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("host1")]

        with mock.patch.object(exakms, "mUpdateCacheKey") as update_cache:
            result = exakms.mSearchExaKmsEntries({}, aRefreshKey=True)

        self.assertEqual(len(result), 1)
        update_cache.assert_called_once()

    def test_delete_entry_update_secret_failure(self):
        # Auto-generated test for mDeleteExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry()
        exakms.mUpdateSecret = mock.Mock(return_value=False)
        self.secrets_client.bundle = DummySecretBundle(_make_secret_content({}))

        result = exakms.mDeleteExaKmsEntry(entry)

        self.assertFalse(result)
        exakms.mUpdateSecret.assert_called_once()

    def test_delete_entry_success(self):
        # Auto-generated test for mDeleteExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry()
        exakms.mUpdateSecret = mock.Mock(return_value=True)
        self.secrets_client.bundle = DummySecretBundle(_make_secret_content({}))

        with mock.patch("exabox.exakms.ExaKms.ExaKms.mDeleteExaKmsEntry") as base_delete:
            result = exakms.mDeleteExaKmsEntry(entry)

        self.assertTrue(result)
        base_delete.assert_called_once_with(entry)

    def test_delete_entry_secret_error(self):
        # Auto-generated test for mDeleteExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry()
        self.secrets_client.bundle_error = Exception("boom")

        with self.assertRaises(ExacloudRuntimeError):
            exakms.mDeleteExaKmsEntry(entry)

    def test_insert_entry_create_secret(self):
        # Auto-generated test for mInsertExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry("host2", "user")
        entry.mSetSecretName(None)
        self.secrets_client.bundle_error = Exception("missing")
        exakms.mCreateSecret = mock.Mock(return_value=True)

        result = exakms.mInsertExaKmsEntry(entry)

        self.assertTrue(result)
        exakms.mCreateSecret.assert_called_once()

    def test_insert_entry_updates_secret(self):
        # Auto-generated test for mInsertExaKmsEntry
        secret_data = {"id_rsa.host1.user": {"keyId": "k1", "encData": "e1"}}
        self.secrets_client.bundle = DummySecretBundle(
            _make_secret_content(secret_data))
        exakms = self._build_exakms()
        entry = self._create_entry("host1.exa", "user")
        exakms.mUpdateSecret = mock.Mock(return_value=True)

        result = exakms.mInsertExaKmsEntry(entry)

        self.assertTrue(result)
        exakms.mUpdateSecret.assert_called_once()

    def test_insert_entry_preserve_creation_time(self):
        # Auto-generated test for mInsertExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry("host3.exa", "user")
        entry.mSetCreationTime("2024-02-03 10:20:30")
        self.secrets_client.bundle_error = Exception("missing")
        exakms.mCreateSecret = mock.Mock(return_value=True)

        exakms.mInsertExaKmsEntry(entry, aPreservateCreationTime=True)

        _, _, key_data = exakms.mCreateSecret.call_args[0]
        self.assertEqual(key_data["creationTime"], "2024-02-03 10:20:30")
        self.assertEqual(key_data["hostType"], entry.mGetHostType().name)
        self.assertEqual(key_data["keyValueInfo"], entry.mGetKeyValueInfo())

    def test_backup_missing_vault_id(self):
        # Auto-generated test for mBackup
        context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": None,
            "exakms_backup_key_id": "backup-key",
        })
        exakms = self._build_exakms_with_context(context)
        self.assertFalse(exakms.mBackup())

    def test_backup_missing_key_id(self):
        # Auto-generated test for mBackup
        context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": None,
        })
        exakms = self._build_exakms_with_context(context)
        self.assertFalse(exakms.mBackup())

    def test_restore_backup_missing_config(self):
        # Auto-generated test for mRestoreBackup
        context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": None,
            "exakms_backup_key_id": "backup-key",
        })
        exakms = self._build_exakms_with_context(context)
        self.assertFalse(exakms.mRestoreBackup())

    def test_restore_backup_missing_key_id(self):
        # Auto-generated test for mRestoreBackup
        context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": None,
        })
        exakms = self._build_exakms_with_context(context)
        self.assertFalse(exakms.mRestoreBackup())

    def test_backup_success(self):
        # Auto-generated test for mBackup
        exakms = self._build_exakms()
        self.vault._secrets = [
            DummySecretSummary("s1"),
            DummySecretSummary("s2"),
        ]

        with mock.patch.object(exakms, "mCopySecretContent") as copy_secret:
            result = exakms.mBackup()

        self.assertTrue(result)
        copy_secret.assert_has_calls([mock.call("s1"), mock.call("s2")])

    def test_restore_backup_success(self):
        # Auto-generated test for mRestoreBackup
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("s1")]

        with mock.patch.object(exakms, "mCopySecretContent") as copy_secret, \
             mock.patch.object(exakms, "mSearchExaKmsEntries") as search_entries:
            result = exakms.mRestoreBackup()

        self.assertTrue(result)
        copy_secret.assert_called_once_with("s1", aBackupVault=True)
        search_entries.assert_called_once_with({}, aRefreshKey=True)

    def test_get_entries_from_secret_strict_and_user(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
                "version": "RSA",
                "hash": "hash1",
                "creationTime": "2024-01-01 00:00:00",
                "label": "lab1",
                "exacloud_host": "exa1",
                "hostType": "DOM0",
                "keyValueInfo": {"a": "b"},
            },
            "id_rsa.other.user2": {
                "keyId": "k2",
                "encData": "e2",
            },
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))

        entries = exakms.mGetEntriesFromSecret(bundle, "host1.exa",
                                               aStrict=True, aUser="user1")

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.mGetUser(), "user1")
        self.assertEqual(entry.mGetSecretName(), "host1.exa")
        self.assertEqual(entry.mGetHostType(), ExaKmsHostType.DOM0)

    def test_get_entries_from_secret_invalid_json(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        invalid = base64.b64encode(b"not-json").decode("utf-8")
        bundle = DummySecretBundle(invalid)

        entries = exakms.mGetEntriesFromSecret(bundle, "host1.exa")

        self.assertEqual(entries, [])

    def test_get_entries_from_secret_defaults(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        secret_data = {
            "id_rsa.host2.user1": {
                "keyId": "k1",
                "encData": "e1",
                "creationTime": "2024-02-02 00:00:00",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))

        entries = exakms.mGetEntriesFromSecret(bundle, "host2.exa")

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.mGetUser(), "user1")
        self.assertEqual(entry.mGetSecretName(), "host2.exa")
        self.assertEqual(entry.mGetCreationTime(), "2024-02-02 00:00:00")

    def test_get_entries_from_secret_strict_skip(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))

        entries = exakms.mGetEntriesFromSecret(bundle, "other",
                                               aStrict=True)

        self.assertEqual(entries, [])

    def test_update_secret_remove_missing_key(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        result = exakms.mUpdateSecret(bundle, "missing", {})

        self.assertFalse(result)
        self.assertEqual(len(self.vault.update_calls), 0)

    def test_update_secret_add_key(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        result = exakms.mUpdateSecret(bundle, "id_rsa.host.new", {"k": "v"})

        self.assertTrue(result)
        self.assertEqual(len(self.vault.update_calls), 1)

    def test_update_secret_remove_key(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        result = exakms.mUpdateSecret(bundle, "id_rsa.host.user", {})

        self.assertTrue(result)
        self.assertEqual(len(self.vault.update_calls), 1)

    def test_update_secret_add_key_triggers_cleanup(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        with mock.patch.object(exakms, "mDeleteSecretVersions") as delete_versions:
            result = exakms.mUpdateSecret(bundle, "id_rsa.host.new", {"k": "v"})

        self.assertTrue(result)
        delete_versions.assert_called_once()

    def test_create_secret_success(self):
        # Auto-generated test for mCreateSecret
        exakms = self._build_exakms()

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations"
        ) as vault_comp:
            vault_comp.return_value = DummyVaultComposite(self.vault)
            result = exakms.mCreateSecret("secret-name", "key-name", {"k": "v"})

        self.assertTrue(result)
        self.assertEqual(len(vault_comp.return_value.calls), 1)

    def test_create_secret_failure_logs_and_raises(self):
        # Auto-generated test for mCreateSecret
        exakms = self._build_exakms()

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations",
            side_effect=Exception("boom"),
        ), mock.patch("exabox.exakms.ExaKmsSIV.ebLogError") as log_error:
            with self.assertRaises(ExacloudRuntimeError):
                exakms.mCreateSecret("secret-name", "key-name", {"k": "v"})

        log_error.assert_called_once()

    def test_update_secret_error(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({})
        bundle = DummySecretBundle(secret_content)
        self.vault._update_error = Exception("boom")

        with self.assertRaises(ExacloudRuntimeError):
            exakms.mUpdateSecret(bundle, "id_rsa.host.user", {"a": "b"})

    def test_delete_secret_versions_limit_exceeded(self):
        # Auto-generated test for mDeleteSecretVersions
        error = oci.exceptions.ServiceError(400, "LimitExceeded", {}, "limit")
        version = DummySecretVersion("sid", "v1", ["DEPRECATED"], None)
        self.vault = DummyVault(versions=[version], schedule_error=error)
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(self.vault.scheduled, [])

    def test_delete_secret_versions_skip_non_deprecated(self):
        # Auto-generated test for mDeleteSecretVersions
        version = DummySecretVersion("sid", "v1", ["CURRENT"], None)
        self.vault = DummyVault(versions=[version])
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(self.vault.scheduled, [])

    def test_delete_secret_versions_warns_on_error(self):
        # Auto-generated test for mDeleteSecretVersions
        error = oci.exceptions.ServiceError(500, "Boom", {}, "boom")
        version = DummySecretVersion("sid", "v1", ["DEPRECATED"], None)
        self.vault = DummyVault(versions=[version], schedule_error=error)
        self.factory.get_vault_client.return_value = self.vault

        with mock.patch("exabox.exakms.ExaKmsSIV.ebLogWarn") as log_warn:
            exakms = self._build_exakms()
            exakms.mDeleteSecretVersions(
                DummySecretBundle(_make_secret_content({})))

        log_warn.assert_called_once()

    def test_copy_secret_content_empty(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        self.secrets_client.bundle = DummySecretBundle(_make_secret_content({}))

        exakms.mCopySecretContent("secret1")

        self.assertEqual(self.vault.update_calls, [])

    def test_copy_secret_content_create(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                Exception("missing"),
            ]
        )

        exakms.mCopySecretContent("secret1")

        self.assertEqual(len(self.vault.update_calls), 0)

    def test_copy_secret_content_updates_existing(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                mock.Mock(data=DummySecretBundle(content, secret_id="s2")),
            ]
        )

        with mock.patch.object(exakms, "mDeleteSecretVersions") as delete_versions:
            exakms.mCopySecretContent("secret2")

        self.assertEqual(len(self.vault.update_calls), 1)
        delete_versions.assert_called_once()

    def test_copy_secret_content_from_backup_vault(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                Exception("missing"),
            ]
        )

        exakms.mCopySecretContent("secret3", aBackupVault=True)

        self.assertEqual(len(self.vault.update_calls), 0)

    def test_cleanup_vault(self):
        # Auto-generated test for mCleanUpVault
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("s1"), DummySecretSummary("s2")]

        exakms.mCleanUpVault()

        self.assertEqual(len(self.vault.update_calls), 2)

    def test_exakms_entry_class_selection(self):
        # Auto-generated test for mBuildExaKmsEntry
        exakms = self._build_exakms()

        entry_default = exakms.mBuildExaKmsEntry("host", "user", "")
        entry_rsa = exakms.mBuildExaKmsEntry("host", "user", "",
                                            aClassName="RSA")
        entry_ecdsa = exakms.mBuildExaKmsEntry("host", "user", "",
                                              aClassName="ECDSA")

        self.assertEqual(entry_default.mGetUser(), "user")
        self.assertEqual(entry_rsa.__class__.__name__, "ExaKmsEntrySIVRSA")
        self.assertEqual(entry_ecdsa.__class__.__name__, "ExaKmsEntrySIVECDSA")

    def test_get_secrets_client(self):
        # Auto-generated test for mGetSecretsClient
        exakms = self._build_exakms()

        self.assertIs(exakms.mGetSecretsClient(), self.secrets_client)

    def test_init_requires_config(self):
        # Auto-generated test for __init__
        bad_context = DummyContext({"kms_key_id": None})
        self.gcontext_patch.stop()
        with mock.patch("exabox.exakms.ExaKmsSIV.get_gcontext",
                        return_value=bad_context):
            with self.assertRaises(ValueError):
                ExaKmsSIV()

    def test_init_requires_vault_id(self):
        # Auto-generated test for __init__
        bad_context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": None,
            "exakms_compartment_id": "compartment-1",
        })
        self.gcontext_patch.stop()
        with mock.patch("exabox.exakms.ExaKmsSIV.get_gcontext",
                        return_value=bad_context):
            with self.assertRaises(ValueError):
                ExaKmsSIV()

    def test_init_requires_compartment_id(self):
        # Auto-generated test for __init__
        bad_context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": None,
        })
        self.gcontext_patch.stop()
        with mock.patch("exabox.exakms.ExaKmsSIV.get_gcontext",
                        return_value=bad_context):
            with self.assertRaises(ValueError):
                ExaKmsSIV()

    def test_enable_fetch_clustername_decorator(self):
        # Auto-generated test for exakms_enable_fetch_clustername_decorator
        context = DummyRegContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": "backup-key",
        })
        exakms = self._build_exakms_with_context(context)

        with mock.patch.object(exakms, "mCalculateDefaultKeyFormat",
                               return_value="RSA") as calc_default:
            result = exakms.mGetDefaultKeyFormat()

        self.assertEqual(result, "RSA")
        calc_default.assert_called_once()
        self.assertFalse(context.mCheckRegEntry("exakms_enable_fetch_clustername"))

    def test_search_entries_strict_matches_short_name(self):
        # Auto-generated test for mSearchExaKmsEntries
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))
        self.secrets_client.bundle = bundle
        exakms = self._build_exakms()

        entries = exakms.mSearchExaKmsEntries({
            "FQDN": "host1",
            "strict": True,
        }, aRefreshKey=True)

        self.assertEqual(len(entries), 1)

    def test_search_entries_filter_all_secrets_strict(self):
        # Auto-generated test for mSearchExaKmsEntries
        self.vault._secrets = [DummySecretSummary("host1"), DummySecretSummary("host2")]
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
            }
        }
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(_make_secret_content(secret_data))),
                mock.Mock(data=DummySecretBundle(_make_secret_content(secret_data))),
            ]
        )
        exakms = self._build_exakms()

        entries = exakms.mSearchExaKmsEntries({
            "strict": True,
        }, aRefreshKey=True)

        self.assertEqual(len(entries), 1)

    def test_copy_secret_content_create_from_backup(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                Exception("missing"),
            ]
        )

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations"
        ) as vault_comp:
            vault_comp.return_value = DummyVaultComposite(self.vault)
            exakms.mCopySecretContent("secret4", aBackupVault=True)

        self.assertEqual(len(vault_comp.return_value.calls), 1)

    def test_delete_secret_versions_skip_scheduled(self):
        # Auto-generated test for mDeleteSecretVersions
        version = DummySecretVersion(
            "sid", "v1", ["DEPRECATED"], time_of_deletion="2024-02-02")
        self.vault = DummyVault(versions=[version])
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(self.vault.scheduled, [])

    def test_delete_secret_versions_success(self):
        # Auto-generated test for mDeleteSecretVersions
        version = DummySecretVersion("sid", "v2", ["DEPRECATED"], None)
        self.vault = DummyVault(versions=[version])
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(len(self.vault.scheduled), 1)
        scheduled = self.vault.scheduled[0]
        self.assertEqual(scheduled[0], "sid")
        self.assertEqual(scheduled[1], "v2")

    def test_list_secrets_pagination(self):
        # Auto-generated test for mListSecrets
        exakms = self._build_exakms()
        page1 = DummyResponse([DummySecretSummary("s1")], True, "next")
        page2 = DummyResponse([DummySecretSummary("s2")], False, None)
        self.vault.list_secrets = mock.Mock(side_effect=[page1, page2])

        secrets = exakms.mListSecrets()

        self.assertEqual([s.secret_name for s in secrets], ["s1", "s2"])

    def test_search_entries_unmask_nat_host(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        exakms.mFilterCache = mock.Mock(return_value=[])

        self.secrets_client.bundle = DummySecretBundle(_make_secret_content({}))

        with mock.patch.object(exakms.mGetEntryClass(), "mUnmaskNatHost",
                               return_value="realhost") as unmask:
            entries = exakms.mSearchExaKmsEntries({"FQDN": "nat-host"},
                                                  aRefreshKey=True)

        self.assertEqual(entries, [])
        unmask.assert_called_once_with("nat-host")
        exakms.mFilterCache.assert_not_called()

    def test_search_entries_cache_refresh_bypasses_cache(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        exakms.mFilterCache = mock.Mock(return_value=[self._create_entry()])

        with mock.patch.object(exakms, "mListSecrets", return_value=[]):
            result = exakms.mSearchExaKmsEntries({}, aRefreshKey=True)

        self.assertEqual(result, [])
        exakms.mFilterCache.assert_not_called()

    def test_search_entries_all_secrets_missing_version_defaults_rsa(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("host1.exa")]
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
            }
        }
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            return_value=mock.Mock(
                data=DummySecretBundle(_make_secret_content(secret_data)))
        )

        entries = exakms.mSearchExaKmsEntries({}, aRefreshKey=True)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].mGetFQDN(), "host1.exa")

    def test_delete_entry_secret_name_defaults_to_fqdn(self):
        # Auto-generated test for mDeleteExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry("host99.exa", "opc")
        entry.mSetSecretName(None)
        entry.mGetSecretName = mock.Mock(return_value=None)
        exakms.mUpdateSecret = mock.Mock(return_value=True)
        self.secrets_client.bundle = DummySecretBundle(_make_secret_content({}))
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            return_value=mock.Mock(data=self.secrets_client.bundle)
        )

        exakms.mDeleteExaKmsEntry(entry)

        self.secrets_client.get_secret_bundle_by_name.assert_called_once_with(
            None, "vault-1")

    def test_update_secret_add_key_updates_payload(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        exakms.mUpdateSecret(bundle, "id_rsa.host.new", {"k": "v"})

        _, update_details = self.vault.update_calls[0]
        updated = json.loads(
            base64.b64decode(update_details.secret_content.content.encode("utf-8"))
            .decode("utf-8"))
        self.assertIn("id_rsa.host.new", updated)
        self.assertEqual(updated["id_rsa.host.new"], {"k": "v"})

    def test_create_secret_uses_expected_details(self):
        # Auto-generated test for mCreateSecret
        exakms = self._build_exakms()

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations"
        ) as vault_comp:
            vault_comp.return_value = DummyVaultComposite(self.vault)
            exakms.mCreateSecret("secret-name", "key-name", {"k": "v"})

        create_details, wait_states = vault_comp.return_value.calls[0]
        self.assertEqual(create_details.secret_name, "secret-name")
        decoded = json.loads(
            base64.b64decode(create_details.secret_content.content.encode("utf-8"))
            .decode("utf-8"))
        self.assertEqual(decoded, {"key-name": {"k": "v"}})
        self.assertIn(oci.vault.models.Secret.LIFECYCLE_STATE_ACTIVE, wait_states)

    def test_search_entries_filters_host_type(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
                "hostType": "DOMU",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))

        entries = exakms.mGetEntriesFromSecret(bundle, "host1")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].mGetHostType(), ExaKmsHostType.DOMU)

    def test_update_secret_remove_entry_success(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        with mock.patch.object(exakms, "mDeleteSecretVersions") as delete_versions:
            result = exakms.mUpdateSecret(bundle, "id_rsa.host.user", {})

        self.assertTrue(result)
        delete_versions.assert_called_once()

    def test_copy_secret_content_updates_existing_from_backup(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                mock.Mock(data=DummySecretBundle(content, secret_id="bk")),
            ]
        )

        with mock.patch.object(exakms, "mDeleteSecretVersions") as delete_versions:
            exakms.mCopySecretContent("secret5", aBackupVault=True)

        self.assertEqual(len(self.vault.update_calls), 1)
        delete_versions.assert_called_once()

    def test_search_entries_with_user_and_strict_filters(self):
        # Auto-generated test for mSearchExaKmsEntries
        bundle = DummySecretBundle(_make_secret_content({}))
        self.secrets_client.bundle = bundle
        exakms = self._build_exakms()

        with mock.patch.object(exakms, "mGetEntriesFromSecret",
                               return_value=["entry"]) as get_entries:
            result = exakms.mSearchExaKmsEntries(
                {"FQDN": "host1", "user": "opc", "strict": True},
                aRefreshKey=True)

        self.assertEqual(result, ["entry"])
        get_entries.assert_called_once_with(bundle, "host1", True, "opc")

    def test_copy_secret_content_empty_backup(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            return_value=mock.Mock(
                data=DummySecretBundle(_make_secret_content({})))
        )

        exakms.mCopySecretContent("secret-empty", aBackupVault=True)

        self.secrets_client.get_secret_bundle_by_name.assert_called_once_with(
            "secret-empty", "backup-vault")
        self.assertEqual(self.vault.update_calls, [])

    def test_cleanup_vault_backup(self):
        # Auto-generated test for mCleanUpVault
        exakms = self._build_exakms()
        secrets = [DummySecretSummary("s1"), DummySecretSummary("s2")]

        with mock.patch.object(exakms, "mListSecrets",
                               return_value=secrets) as list_secrets:
            exakms.mCleanUpVault(aBackupVault=True)

        list_secrets.assert_called_once_with(aBackupVault=True)
        self.assertEqual(len(self.vault.update_calls), 2)

    def test_copy_secret_content_create_main_vault(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                Exception("missing"),
            ]
        )

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations"
        ) as vault_comp:
            vault_comp.return_value = DummyVaultComposite(self.vault)
            exakms.mCopySecretContent("secret-create")

        self.assertEqual(len(vault_comp.return_value.calls), 1)

    def test_copy_secret_content_updates_main_vault(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                mock.Mock(data=DummySecretBundle(content, secret_id="main")),
            ]
        )

        with mock.patch.object(exakms, "mDeleteSecretVersions") as delete_versions:
            exakms.mCopySecretContent("secret-update")

        self.assertEqual(len(self.vault.update_calls), 1)
        delete_versions.assert_called_once()

    def test_init_missing_kms_key_id(self):
        # Auto-generated test for __init__
        context = DummyContext({
            "kms_key_id": None,
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": "backup-key",
        })

        with self.assertRaises(ValueError):
            self._build_exakms_with_context(context)


    def test_list_secrets_backup_vault_calls_vault_id(self):
        # Auto-generated test for mListSecrets
        exakms = self._build_exakms()
        self.vault.list_secrets = mock.Mock(
            return_value=DummyResponse([DummySecretSummary("s1")], False, None)
        )

        exakms.mListSecrets(aBackupVault=True)

        self.vault.list_secrets.assert_called_once_with(
            page=None, vault_id="backup-vault",
            compartment_id="compartment-1")

    def test_insert_entry_update_preserve_creation_time(self):
        # Auto-generated test for mInsertExaKmsEntry
        secret_data = {"id_rsa.host9.user": {"keyId": "k1", "encData": "e1"}}
        self.secrets_client.bundle = DummySecretBundle(
            _make_secret_content(secret_data))
        exakms = self._build_exakms()
        entry = self._create_entry("host9.exa", "user")
        entry.mSetCreationTime("2024-03-03 03:03:03")
        exakms.mUpdateSecret = mock.Mock(return_value=True)

        with mock.patch(
            "exabox.exakms.ExaKms.ExaKms.mInsertExaKmsEntry"
        ) as base_insert:
            result = exakms.mInsertExaKmsEntry(entry,
                                               aPreservateCreationTime=True)

        self.assertTrue(result)
        base_insert.assert_called_once_with(entry)
        _, _, key_data = exakms.mUpdateSecret.call_args[0]
        self.assertEqual(key_data["creationTime"], "2024-03-03 03:03:03")
        self.assertEqual(key_data["hostType"], entry.mGetHostType().name)

    def test_init_missing_vault_id(self):
        # Auto-generated test for __init__
        context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": None,
            "exakms_compartment_id": "compartment-1",
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": "backup-key",
        })

        with self.assertRaises(ValueError):
            self._build_exakms_with_context(context)

    def test_init_missing_compartment_id(self):
        # Auto-generated test for __init__
        context = DummyContext({
            "kms_key_id": "kms-key",
            "exakms_vault_id": "vault-1",
            "exakms_compartment_id": None,
            "exakms_backup_vault_id": "backup-vault",
            "exakms_backup_key_id": "backup-key",
        })

        with self.assertRaises(ValueError):
            self._build_exakms_with_context(context)

    def test_get_entries_from_secret_user_filtered_out(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        secret_data = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))

        entries = exakms.mGetEntriesFromSecret(bundle, "host1", aUser="user2")

        self.assertEqual(entries, [])

    def test_search_entries_sort_and_cache(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        self.vault._secrets = [
            DummySecretSummary("host1.exa"),
            DummySecretSummary("host2.exa"),
        ]
        secret1 = {
            "id_rsa.host1.user1": {
                "keyId": "k1",
                "encData": "e1",
                "creationTime": "2024-01-01 00:00:00",
            }
        }
        secret2 = {
            "id_rsa.host2.user1": {
                "keyId": "k2",
                "encData": "e2",
                "creationTime": "2025-01-01 00:00:00",
            }
        }
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(_make_secret_content(secret1))),
                mock.Mock(data=DummySecretBundle(_make_secret_content(secret2))),
            ]
        )

        with mock.patch.object(exakms, "mUpdateCacheKey") as update_cache:
            entries = exakms.mSearchExaKmsEntries({"strict": True},
                                                  aRefreshKey=True)

        self.assertEqual([entry.mGetFQDN() for entry in entries],
                         ["host2.exa", "host1.exa"])
        self.assertEqual(update_cache.call_count, 2)

    def test_copy_secret_content_create_calls_composite(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                Exception("missing"),
            ]
        )

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.oci.vault.VaultsClientCompositeOperations"
        ) as vault_comp:
            vault_comp.return_value = DummyVaultComposite(self.vault)
            exakms.mCopySecretContent("secret-create")

        self.assertEqual(len(vault_comp.return_value.calls), 1)

    def test_delete_secret_versions_skip_scheduled(self):
        # Auto-generated test for mDeleteSecretVersions
        version = DummySecretVersion("sid", "v1", ["DEPRECATED"],
                                     time_of_deletion="2024-01-01T00:00:00Z")
        self.vault = DummyVault(versions=[version])
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(self.vault.scheduled, [])

    def test_insert_entry_update_secret_failure(self):
        # Auto-generated test for mInsertExaKmsEntry
        secret_data = {"id_rsa.host1.user": {"keyId": "k1", "encData": "e1"}}
        self.secrets_client.bundle = DummySecretBundle(
            _make_secret_content(secret_data))
        exakms = self._build_exakms()
        entry = self._create_entry("host1.exa", "user")
        exakms.mUpdateSecret = mock.Mock(return_value=False)

        with mock.patch("exabox.exakms.ExaKms.ExaKms.mInsertExaKmsEntry") as base_insert:
            result = exakms.mInsertExaKmsEntry(entry)

        self.assertFalse(result)
        base_insert.assert_not_called()

    def test_insert_entry_create_secret_failure(self):
        # Auto-generated test for mInsertExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry("host2.exa", "user")
        entry.mSetSecretName(None)
        self.secrets_client.bundle_error = Exception("missing")
        exakms.mCreateSecret = mock.Mock(return_value=False)

        with mock.patch("exabox.exakms.ExaKms.ExaKms.mInsertExaKmsEntry") as base_insert:
            result = exakms.mInsertExaKmsEntry(entry)

        self.assertFalse(result)
        base_insert.assert_not_called()

    def test_get_entries_from_secret_ecdsa_version(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        secret_data = {
            "id_rsa.host3.user3": {
                "keyId": "k3",
                "encData": "e3",
                "version": "ECDSA",
            }
        }
        bundle = DummySecretBundle(_make_secret_content(secret_data))

        entries = exakms.mGetEntriesFromSecret(bundle, "host3")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].__class__.__name__, "ExaKmsEntrySIVECDSA")

    def test_delete_secret_versions_warns_on_error(self):
        # Auto-generated test for mDeleteSecretVersions
        error = oci.exceptions.ServiceError(500, "InternalError", {}, "boom")
        version = DummySecretVersion("sid", "v1", ["DEPRECATED"], None)
        self.vault = DummyVault(versions=[version], schedule_error=error)
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()

        with mock.patch("exabox.exakms.ExaKmsSIV.ebLogWarn") as log_warn:
            exakms.mDeleteSecretVersions(
                DummySecretBundle(_make_secret_content({})))

        log_warn.assert_called_once_with("Unable to delete secret version")

    def test_copy_secret_content_empty_main_vault(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            return_value=mock.Mock(
                data=DummySecretBundle(_make_secret_content({})))
        )

        exakms.mCopySecretContent("secret-empty")

        self.secrets_client.get_secret_bundle_by_name.assert_called_once_with(
            "secret-empty", "vault-1")
        self.assertEqual(self.vault.update_calls, [])

    def test_cleanup_vault_main(self):
        # Auto-generated test for mCleanUpVault
        exakms = self._build_exakms()
        secrets = [DummySecretSummary("s1"), DummySecretSummary("s2")]

        with mock.patch.object(exakms, "mListSecrets",
                               return_value=secrets) as list_secrets:
            exakms.mCleanUpVault()

        list_secrets.assert_called_once_with(aBackupVault=False)
        self.assertEqual(len(self.vault.update_calls), 2)

    def test_build_exakms_entry_class_override(self):
        # Auto-generated test for mBuildExaKmsEntry
        exakms = self._build_exakms()

        ecdsa_entry = exakms.mBuildExaKmsEntry("host1", "user1", "",
                                              aClassName="ECDSA")
        rsa_entry = exakms.mBuildExaKmsEntry("host2", "user2", "",
                                            aClassName="RSA")

        self.assertEqual(ecdsa_entry.__class__.__name__, "ExaKmsEntrySIVECDSA")
        self.assertEqual(rsa_entry.__class__.__name__, "ExaKmsEntrySIVRSA")

    def test_get_entries_from_secret_invalid_json(self):
        # Auto-generated test for mGetEntriesFromSecret
        exakms = self._build_exakms()
        bad_content = base64.b64encode(b"not-json").decode("utf-8")
        bundle = DummySecretBundle(bad_content)

        with mock.patch("exabox.exakms.ExaKmsSIV.ebLogWarn") as log_warn:
            entries = exakms.mGetEntriesFromSecret(bundle, "secret-bad")

        self.assertEqual(entries, [])
        log_warn.assert_called_once_with(
            "Secret secret-bad is not a valid json")

    def test_update_secret_remove_missing_key_logs_info(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        with mock.patch("exabox.exakms.ExaKmsSIV.ebLogInfo") as log_info:
            result = exakms.mUpdateSecret(bundle, "missing", {})

        self.assertFalse(result)
        self.assertEqual(len(self.vault.update_calls), 0)
        self.assertIn("missing", log_info.call_args[0][0])

    def test_delete_secret_versions_paginated(self):
        # Auto-generated test for mDeleteSecretVersions
        version1 = DummySecretVersion("sid", "v1", ["DEPRECATED"], None)
        version2 = DummySecretVersion("sid", "v2", ["DEPRECATED"], None)
        page1 = DummyResponse([version1], True, "next")
        page2 = DummyResponse([version2], False, None)
        self.vault = DummyVault()
        self.vault.list_secret_versions = mock.Mock(side_effect=[page1, page2])
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(len(self.vault.scheduled), 2)
        self.assertEqual(
            self.vault.list_secret_versions.call_args_list,
            [mock.call("secret-1", page=None), mock.call("secret-1", page="next")])

    def test_insert_entry_create_secret_uses_current_metadata(self):
        # Auto-generated test for mInsertExaKmsEntry
        exakms = self._build_exakms()
        entry = self._create_entry("host4.exa", "user")
        entry.mSetSecretName(None)
        self.secrets_client.bundle_error = Exception("missing")
        exakms.mCreateSecret = mock.Mock(return_value=True)

        with mock.patch(
            "exabox.exakms.ExaKmsSIV.ExaKmsEntrySIVRSA.mGetCurrentTime",
            return_value="2026-02-26 10:11:12",
        ), mock.patch(
            "exabox.exakms.ExaKmsSIV.ExaKmsEntrySIVRSA.mGetCurrentLabel",
            return_value="label-now",
        ), mock.patch(
            "exabox.exakms.ExaKmsSIV.ExaKmsEntrySIVRSA.mGetCurrentExacloudHost",
            return_value="host-now",
        ), mock.patch(
            "exabox.exakms.ExaKms.ExaKms.mInsertExaKmsEntry"
        ) as base_insert:
            result = exakms.mInsertExaKmsEntry(entry)

        self.assertTrue(result)
        base_insert.assert_called_once_with(entry)
        _, _, key_data = exakms.mCreateSecret.call_args[0]
        self.assertEqual(key_data["creationTime"], "2026-02-26 10:11:12")
        self.assertEqual(key_data["label"], "label-now")
        self.assertEqual(key_data["exacloud_host"], "host-now")
        self.assertEqual(key_data["hostType"], entry.mGetHostType().name)

    def test_insert_entry_update_secret_calls_base_insert(self):
        # Auto-generated test for mInsertExaKmsEntry
        secret_data = {"id_rsa.host5.user": {"keyId": "k1", "encData": "e1"}}
        self.secrets_client.bundle = DummySecretBundle(
            _make_secret_content(secret_data))
        exakms = self._build_exakms()
        entry = self._create_entry("host5.exa", "user")
        exakms.mUpdateSecret = mock.Mock(return_value=True)

        with mock.patch(
            "exabox.exakms.ExaKms.ExaKms.mInsertExaKmsEntry"
        ) as base_insert:
            result = exakms.mInsertExaKmsEntry(entry)

        self.assertTrue(result)
        base_insert.assert_called_once_with(entry)

    def test_search_entries_all_secrets_propagates_error(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("host1")]
        error = oci.exceptions.ServiceError(404, "NotAuthorizedOrNotFound",
                                            {}, "not found")
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=error
        )

        with self.assertRaises(oci.exceptions.ServiceError):
            exakms.mSearchExaKmsEntries({}, aRefreshKey=True)

        self.secrets_client.get_secret_bundle_by_name.assert_called_once_with(
            "host1", "vault-1")

    def test_update_secret_remove_missing_logs(self):
        # Auto-generated test for mUpdateSecret
        exakms = self._build_exakms()
        secret_content = _make_secret_content({"id_rsa.host.user": {"a": "b"}})
        bundle = DummySecretBundle(secret_content)

        with mock.patch("exabox.exakms.ExaKmsSIV.ebLogInfo") as log_info:
            result = exakms.mUpdateSecret(bundle, "id_rsa.host.other", {})

        self.assertFalse(result)
        self.assertEqual(len(self.vault.update_calls), 0)
        log_info.assert_called_once()

    def test_delete_secret_versions_skips_scheduled_deletion(self):
        # Auto-generated test for mDeleteSecretVersions
        version = DummySecretVersion("sid", "v1", ["DEPRECATED"], "2024-01-01")
        self.vault = DummyVault(versions=[version])
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        self.assertEqual(self.vault.scheduled, [])

    def test_copy_secret_content_updates_from_backup_vault(self):
        # Auto-generated test for mCopySecretContent
        exakms = self._build_exakms()
        content = _make_secret_content({"id_rsa.host.user": {"k": "v"}})
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(content)),
                mock.Mock(data=DummySecretBundle(content, secret_id="backup-id")),
            ]
        )

        with mock.patch.object(exakms, "mDeleteSecretVersions") as delete_versions:
            exakms.mCopySecretContent("secret-backup", aBackupVault=True)

        self.assertEqual(len(self.vault.update_calls), 1)
        delete_versions.assert_called_once()

    def test_cleanup_vault_backup_path(self):
        # Auto-generated test for mCleanUpVault
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("s1"), DummySecretSummary("s2")]

        exakms.mCleanUpVault(aBackupVault=True)

        self.assertEqual(len(self.vault.update_calls), 2)

    def test_build_exakms_entry_class_selection(self):
        # Auto-generated test for mBuildExaKmsEntry
        exakms = self._build_exakms()

        with mock.patch.object(ExaKmsEntrySIVECDSA, "mSetPrivateKey"), \
             mock.patch.object(ExaKmsEntrySIVRSA, "mSetPrivateKey"):
            ecdsa_entry = exakms.mBuildExaKmsEntry("host1", "opc", "key",
                                                  aClassName="ECDSA")
            rsa_entry = exakms.mBuildExaKmsEntry("host2", "opc", "key",
                                                 aClassName="RSA")

        self.assertIsInstance(ecdsa_entry, ExaKmsEntrySIVECDSA)
        self.assertIsInstance(rsa_entry, ExaKmsEntrySIVRSA)

    def test_search_entries_all_secrets_sorted_and_cached(self):
        # Auto-generated test for mSearchExaKmsEntries
        exakms = self._build_exakms()
        self.vault._secrets = [DummySecretSummary("s1"), DummySecretSummary("s2")]
        entry_old = self._create_entry("host-old", "user")
        entry_old.mSetCreationTime("2024-01-01 00:00:00")
        entry_new = self._create_entry("host-new", "user")
        entry_new.mSetCreationTime("2024-05-01 00:00:00")
        self.secrets_client.get_secret_bundle_by_name = mock.Mock(
            side_effect=[
                mock.Mock(data=DummySecretBundle(_make_secret_content({}))),
                mock.Mock(data=DummySecretBundle(_make_secret_content({}))),
            ]
        )

        with mock.patch.object(exakms, "mFilterCache", return_value=[]), \
             mock.patch.object(exakms, "mGetEntriesFromSecret",
                               side_effect=[[entry_old], [entry_new]]), \
             mock.patch.object(exakms, "mUpdateCacheKey") as update_cache:
            entries = exakms.mSearchExaKmsEntries({}, aRefreshKey=False)

        self.assertEqual([e.mGetFQDN() for e in entries],
                         ["host-new", "host-old"])
        update_cache.assert_has_calls([
            mock.call("host-new", entry_new),
            mock.call("host-old", entry_old),
        ], any_order=True)

    def test_delete_secret_versions_warns_on_error(self):
        # Auto-generated test for mDeleteSecretVersions
        error = oci.exceptions.ServiceError(500, "InternalError", {}, "boom")
        version = DummySecretVersion("sid", "v1", ["DEPRECATED"], None)
        self.vault = DummyVault(versions=[version], schedule_error=error)
        self.factory.get_vault_client.return_value = self.vault

        exakms = self._build_exakms()
        with mock.patch("exabox.exakms.ExaKmsSIV.ebLogWarn") as log_warn:
            exakms.mDeleteSecretVersions(DummySecretBundle(_make_secret_content({})))

        log_warn.assert_called_once_with("Unable to delete secret version")


if __name__ == "__main__":
    unittest.main()
