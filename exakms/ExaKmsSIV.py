#!/bin/python
#
# $Header: ecs/exacloud/exabox/exakms/ExaKmsSIV.py /main/6 2023/10/24 09:29:02 jesandov Exp $
#
# ExaKmsSIV.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ExaKmsSIV.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    10/20/23 - 35933990: Include label in ExaKmsEntry
#    jesandov    06/12/23 - 35484161: Add validation to nathostname in the search pattern dict
#    jesandov    04/27/23 - 35141575: Add support of ECDSA key type
#    alsepulv    04/21/22 - Creation
#

import base64
from datetime import datetime, timedelta, timezone
import json
import oci
import copy
from oci.vault.models import (Base64SecretContentDetails, CreateSecretDetails,
                             ScheduleSecretDeletionDetails, UpdateSecretDetails,
                             ScheduleSecretVersionDeletionDetails)
import re
from typing import List

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.exakms.ExaKms import ExaKms
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.exakms.ExaKmsEntrySIV import ExaKmsEntrySIVRSA, ExaKmsEntrySIVECDSA
from exabox.exakms.ExaKmsHistorySIV import ExaKmsHistorySIV
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn


class ExaKmsSIV(ExaKms):
    def __init__(self):
        """
        Creates a new ExaKmsSIV. This implementation of ExaKms stores keys
        as secrets in an OCI Vault. It holds the following properties:
        - vault_id: OCID of the vault to store the secrets
        - compartment_id: OCID of the compartment
        - key_id: OCID to use for the creation of new secrets
        - signer: Instance Principals signer to create OCI clients
        - vault: OCI Vault Client
        - secrets_client: OCI Secrets Client

        :raises ValueError: If required parameters not set in exabox.conf
        """

        super().__init__()

        _entryClasses = {
            "ECDSA": ExaKmsEntrySIVECDSA,
            "RSA": ExaKmsEntrySIVRSA,
        }

        _entryClasses["DEFAULT"] = _entryClasses["ECDSA"]
        self.mSetEntryClass(_entryClasses)

        if not get_gcontext().mCheckConfigOption("kms_key_id"):
            raise ValueError("'kms_key_id' configure parameter not set in "
                             "exabox.conf")

        if not get_gcontext().mCheckConfigOption("exakms_vault_id"):
            raise ValueError("'exakms_vault_id' configure parameter not set in "
                             "exabox.conf")

        if not get_gcontext().mCheckConfigOption("exakms_compartment_id"):
            raise ValueError("'exakms_compartment_id' configure parameter not "
                             "set in exabox.conf")

        self.__vault_id = get_gcontext().mCheckConfigOption("exakms_vault_id")
        self.__backup_vault_id = get_gcontext().mCheckConfigOption(
                                                      "exakms_backup_vault_id")
        self.__backup_key_id = get_gcontext().mCheckConfigOption(
                                                        "exakms_backup_key_id")
        self.__compartment_id = get_gcontext().mCheckConfigOption(
                                                       "exakms_compartment_id")
        self.__key_id = get_gcontext().mCheckConfigOption("kms_key_id")

        # Create OCI Vault Client and OCI Secrets Client
        _factory = ExaOCIFactory()
        self.__vault = _factory.get_vault_client()
        self.__vault.retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY
        self.__secrets_client = _factory.get_secrets_client()
        self.__secrets_client.retry_strategy = oci.retry.DEFAULT_RETRY_STRATEGY

        self.mSetExaKmsHistoryInstance(ExaKmsHistorySIV(self))

    def mGetSecretsClient(self):
        return self.__secrets_client


    def mBuildExaKmsEntry(self, aFQDN, aUser, aPrivateKey, aHostType=ExaKmsHostType.UNKNOWN, aClassName=None):

        _class = self.mGetEntryClass()

        if aClassName:
            if "ECDSA" in aClassName:
                _class = ExaKmsEntrySIVECDSA
            else:
                _class = ExaKmsEntrySIVRSA

        _entry = _class(aFQDN, aUser, aPrivateKey, aHostType)
        return _entry

    def mSearchExaKmsEntries(self, aPatternDict: dict = {},
                         aRefreshKey: bool = False) -> List[ExaKmsEntrySIVRSA]:
        """
        Method to search ExaKms entries. It uses the filters provided
        in aPatternDict and returns all entries found. If aPatternDict is empty,
        we return all entries. aPatternDict can have one or more of
        the following entries:
        {
            "FQDN": <str> FQDN of a host,
            "user": <str> user name for the key,
            "strict": <bool> whether the match for FQDN should match exactly
        }

        :param aPatternDict: a dictionary used to filter our search
        :param aRefreshKey: if True, we will not search through the cache first

        :returns: a list of ExaKms entries
        """

        _patternDict = copy.deepcopy(aPatternDict)
        if "FQDN" in _patternDict:
            _patternDict["FQDN"] = self.mGetEntryClass().mUnmaskNatHost(_patternDict["FQDN"])

        _entries = []

        # Search in cache first
        if not aRefreshKey:
            _entries = self.mFilterCache(_patternDict)
            if _entries:
                return _entries

        _strict = _patternDict.get("strict", False)

        # Filter with _patternDict
        if "FQDN" in _patternDict:
            _secret_name = _patternDict["FQDN"]
            try:
                _secret = self.__secrets_client.get_secret_bundle_by_name(
                                            _secret_name, self.__vault_id).data
            except oci.exceptions.ServiceError as e:
                if e.status == 404 and e.code == "NotAuthorizedOrNotFound":
                    ebLogWarn(f"No entry found for {_secret_name}")
                    return []
                raise e


            if "user" in _patternDict:
                return self.mGetEntriesFromSecret(_secret, _secret_name,
                                                 _strict, _patternDict["user"])

            return self.mGetEntriesFromSecret(_secret, _secret_name, _strict)

        # Return all exakms keys
        _secrets = self.mListSecrets()

        for _secret_summary in _secrets:
            _secret_name = _secret_summary.secret_name
            _secret = self.__secrets_client.get_secret_bundle_by_name(
                                            _secret_name, self.__vault_id).data
            _entries += self.mGetEntriesFromSecret(_secret, _secret_name,
                                                   _strict)

        # Sort the entries
        _entries = sorted(_entries, key=lambda x: x.mGetCreationTime(),
                          reverse=True)

        # Update the cache
        for _entry in _entries:
            self.mUpdateCacheKey(_entry.mGetFQDN(), _entry)

        return _entries

    def mDeleteExaKmsEntry(self, aKmsEntry: ExaKmsEntrySIVRSA) -> bool:
        """
        Method to remove an exakms entry from ExaKmsSIV

        :param aKmsEntry: exakms entry to remove

        :returns: True if successful, False otherwise

        :raises ExacloudRuntimeError: If unable to remove entry
        """

        _secret_name = aKmsEntry.mGetSecretName()
        _key_name = (f"id_rsa.{aKmsEntry.mGetFQDN().split('.')[0]}."
                     f"{aKmsEntry.mGetUser()}")

        try:
            _secret = self.__secrets_client.get_secret_bundle_by_name(
                                            _secret_name, self.__vault_id).data
        except Exception as e:
            _err_msg = (f"Could not delete exakms key {_key_name}. Error trying"
                        f" to get secret {_secret_name} from OCI vault. {e}")
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

        if self.mUpdateSecret(_secret, _key_name):
            super().mDeleteExaKmsEntry(aKmsEntry)
            return True

        return False

    def mInsertExaKmsEntry(self, aKmsEntry: ExaKmsEntrySIVRSA,
                           aPreservateCreationTime: bool = False) -> bool:
        """
        Method to insert an ExaKms entry into ExaKmsSIV

        :param aKmsEntry: the exakms entry to insert

        :returns: True if successful, False otherwise
        """

        if not aKmsEntry.mGetSecretName():
            aKmsEntry.mSetSecretName(aKmsEntry.mGetFQDN())

        # Search for secret in the vault
        _secret_name = aKmsEntry.mGetSecretName()
        try:
            _secret = self.__secrets_client.get_secret_bundle_by_name(
                                            _secret_name, self.__vault_id).data
        except:
            _secret = None

        # Create dict entry
        _encrypted_key = {}
        _encrypted_key["keyId"] = aKmsEntry.mGetKeyId()
        _encrypted_key["encData"] = aKmsEntry.mGetEncData()
        _encrypted_key["hostType"] = aKmsEntry.mGetHostType().name
        _encrypted_key["keyValueInfo"] = aKmsEntry.mGetKeyValueInfo()
        _encrypted_key["hash"] = aKmsEntry.mGetHash()
        _encrypted_key["label"] = ExaKmsEntrySIVRSA.mGetCurrentLabel()
        _encrypted_key["exacloud_host"] = ExaKmsEntrySIVRSA.mGetCurrentExacloudHost()

        if aPreservateCreationTime:
            _encrypted_key['creationTime'] = aKmsEntry.mGetCreationTime()
        else:
            _encrypted_key['creationTime'] = ExaKmsEntrySIVRSA.mGetCurrentTime()

        _key_name = (f"id_rsa.{aKmsEntry.mGetFQDN().split('.')[0]}."
                     f"{aKmsEntry.mGetUser()}")

        # Push entry into the vault
        _suc = False
        if _secret:
            _suc = self.mUpdateSecret(_secret, _key_name, _encrypted_key)
        else:
            _suc = self.mCreateSecret(_secret_name, _key_name, _encrypted_key)

        if _suc:
            super().mInsertExaKmsEntry(aKmsEntry)

        return _suc

    def mBackup(self) -> bool:
        """
        Method to store a backup of the keys in the backup vault.

        :returns: True if successful. False otherwise
        """

        if not self.__backup_vault_id:
            ebLogError("Error during ExaKms Backup Keys. No backup vault id set"
                       " in exabox.conf with key 'exakms_backup_vault_id'. "
                       "No keys have been backed up.")
            return False

        if not self.__backup_key_id:
            ebLogError("Error during ExaKms Backup Keys. No backup key id set"
                       " in exabox.conf with key 'exakms_backup_key_id'. "
                       "No keys have been backed up.")
            return False

        # List all secrets
        _secrets = self.mListSecrets()

        # Perform backup
        for _secret in _secrets:
            self.mCopySecretContent(_secret.secret_name)

        ebLogInfo("Backup of ExaKms keys complete!")

        return True

    def mRestoreBackup(self) -> bool:
        """
        Method to restore a saved backup of the keys. We take the version to be
        restored of each secret and use that data to update the secret.

        :returns: True if successful. False otherwise
        """

        if not self.__backup_vault_id:
            ebLogError("Error during ExaKms Restore Backup. No backup vault id"
                       " set in exabox.conf with key 'exakms_backup_vault_id'."
                       " No keys have been restored.")
            return False

        if not self.__backup_key_id:
            ebLogError("Error during ExaKms Restore Backup. No backup key id "
                       "set in exabox.conf with key 'exakms_backup_key_id'. "
                       "No keys have been restored.")
            return False

        ebLogInfo("Started restoring ExaKms keys from backup. "
                  "This might take a while")

        _secrets = self.mListSecrets(aBackupVault=True)

        # Perform restore
        for _secret in _secrets:
            self.mCopySecretContent(_secret.secret_name, aBackupVault=True)

        # Refresh cache
        self.mSetCache({})
        self.mSearchExaKmsEntries({}, aRefreshKey=True)

        return True


    ##################
    # INTERNAL METHODS
    ##################

    def mGetEntriesFromSecret(self, aSecret: oci.secrets.models.SecretBundle,
                              aSecretName: str, aStrict: bool = False,
                              aUser: str = "") -> List[ExaKmsEntrySIVRSA]:
        """
        Takes a secret and returns the ExaKms entries stored in it. If aStrict
        is True or aUser is provided, they can be used to filter the result

        :param aSecret: the secret bundle object to be read
        :param ASecretName: the name of the secret
        :param aStrict: if True, we only return entries with FQDN matching
                        with aSecretName
        :param aUser: if provided, it will only return the ExaKms entries
                      for said user
        :returns: a list of ExaKmsEntries
        """

        _entries = []

        try:
            _dict_entries = json.loads(base64.b64decode(
                                  aSecret.secret_bundle_content.content.encode(
                                  "utf-8")).decode("utf-8"))
        except json.decoder.JSONDecodeError:
            ebLogWarn(f"Secret {aSecretName} is not a valid json")
            return []

        for _entry_name, _entry_data in _dict_entries.items():
            _key_pattern = re.match(r"id_rsa.([\w\-\_]+).([\w\-\_]+)",
                                    _entry_name)
            _fqdn = _key_pattern.group(1)
            if '.' in aSecretName:
                _fqdn = aSecretName
            _user = _key_pattern.group(2)

            if aUser and aUser != _user:
                continue

            if aStrict and aSecretName.split(".")[0] != _fqdn.split(".")[0]:
                continue

            _version = None
            if "version" in _entry_data:
                _version = _entry_data["version"]
            else:
                _version = "RSA"

            _entry = self.mBuildExaKmsEntry(_fqdn, _user, "", aClassName=_version)
            _entry.mSetKeyId(_entry_data["keyId"])
            _entry.mSetEncData(_entry_data["encData"])
            _entry.mSetSecretName(aSecretName)

            if "hash" in _entry_data:
                _entry.mSetHash(_entry_data["hash"])

            if "creationTime" in _entry_data:
                _entry.mSetCreationTime(_entry_data["creationTime"])

            if "label" in _entry_data:
                _entry.mSetLabel(_entry_data["label"])

            if "exacloud_host" in _entry_data:
                _entry.mSetExacloudHost(_entry_data["exacloud_host"])

            if "hostType" in _entry_data:
                _entry.mSetHostType(_entry_data["hostType"])

            if "keyValueInfo" in _entry_data:
                _entry.mSetKeyValueInfo(_entry_data["keyValueInfo"])

            _entries.append(_entry)

        return _entries

    def mListSecrets(self, aBackupVault: bool = False) -> List[oci.vault.models.SecretSummary]:
        """
        Returns a list of all the secrets in the main vault.

        :param aBackupVault: if True, it will return a list of all the secrets
                             in the backup vault, instead.
        :returns: a list of all the secrets in the specified vault
        """

        _secrets = []
        _continue = True
        _page = None
        _vault = self.__vault_id

        if aBackupVault:
            _vault = self.__backup_vault_id

        while _continue:
            _resp = self.__vault.list_secrets(page=_page, vault_id=_vault,
                                          compartment_id=self.__compartment_id)
            _secrets += _resp.data
            _continue = _resp.has_next_page
            _page = _resp.next_page

        return _secrets

    def mCreateSecret(self, aSecretName: str, aKeyName: str,
                      aKeyData: dict) -> bool:
        """
        Creates a new secret in the OCI vault with a single entry.

        :param aSecretName: the name to be given to the new secret
        :param aKeyName: the key name to be inserted in the new secret
        :param aKeyData: the key data to be inserted in the new secret

        :returns: True if successful. False otherwise

        :raises ExacloudRuntimeError: If there is an error while
                                      creating the secret
        """

        _secret_data = {aKeyName: aKeyData}

        # Encode data
        _encoded_data = base64.b64encode(
                      json.dumps(_secret_data).encode("utf-8")).decode("utf-8")

        # Create secret
        _secret_content = Base64SecretContentDetails(content_type="BASE64",
                                                     content=_encoded_data)
        _secret_details = CreateSecretDetails(key_id=self.__key_id,
                                          compartment_id=self.__compartment_id,
                                          vault_id=self.__vault_id,
                                          secret_name=aSecretName,
                                          secret_content=_secret_content)

        # Push secret to OCI Vault
        try:
            _vault = oci.vault.VaultsClientCompositeOperations(self.__vault)
            _vault.create_secret_and_wait_for_state(
               create_secret_details=_secret_details,
               wait_for_states=[oci.vault.models.Secret.LIFECYCLE_STATE_ACTIVE])

        except Exception as e:
            _err_msg = ("An error has occured while inserting an exakms entry "
                       f"into the OCI vault. Key: {aKeyName}. {e}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

        ebLogInfo(f"ExaKms entry inserted into OCI Vault. Key {aKeyName}")
        return True

    def mUpdateSecret(self, aSecret: oci.secrets.models.SecretBundle,
                      aKeyName: str, aKeyData: dict = {}) -> bool:
        """
        Updates aKeyName entry in aSecret in the OCI Vault with aKeyData.
        If aKeyData is empty, we remove aKeyName from the secret.

        :param aSecret: the secret to update
        :param aKeyName: the key name to be updated / removed in the secret
        :param aKeyData: if not empty, the key data to be set.

        :returns: True if update / delete was successful. False otherwise

        :raises ExacloudRuntimeError: If there is an error while
                                      updating the secret.
        """

        # Decode and load the secret data into a dict and add new entry
        _secret_data = json.loads(base64.b64decode(
                                  aSecret.secret_bundle_content.content.encode(
                                  "utf-8")).decode("utf-8"))

        if not aKeyData:
            # Remove entry
            if aKeyName in _secret_data:
                del _secret_data[aKeyName]
            else:
                ebLogInfo((f"Cannot remove exakms key {aKeyName}. "
                           "It was not found in OCI Secret / already removed."))
                return False
        else:
           # Add entry
            _secret_data[aKeyName] = aKeyData

        # Encode data
        _encoded_data = base64.b64encode(
                      json.dumps(_secret_data).encode("utf-8")).decode("utf-8")

        # Update secret
        _secret_content = Base64SecretContentDetails(content_type="BASE64",
                                                     content=_encoded_data)
        _secret_details = UpdateSecretDetails(secret_content=_secret_content)

        try:
            # Push secret to OCI Vault
            self.__vault.update_secret(secret_id=aSecret.secret_id,
                                       update_secret_details=_secret_details)
            # Delete previous secret version
            self.mDeleteSecretVersions(aSecret)

        except Exception as e:
            _err_msg = ("An error has occured while updating a secret "
                       f"in the OCI vault. Key: {aKeyName}. {e}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg) from e

        ebLogInfo(f"Secret updated on OCI Vault. Key {aKeyName}")
        return True

    def mDeleteSecretVersions(self, aSecret: oci.secrets.models.SecretBundle) -> None:
        """
        Deletes all deprecated versions of a secret.

        :param aSecret: The secret for which deprecated versions will be deleted
        """

        # List all secret versions
        _versions = []
        _continue = True
        _page = None

        while _continue:
            _resp = self.__vault.list_secret_versions(aSecret.secret_id,
                                                      page=_page)
            _versions += _resp.data
            _continue = _resp.has_next_page
            _page = _resp.next_page

        # Delete any deprecated secret versions
        for _version in _versions:
            # If version is current or previous, or it's already scheduled
            # for deletion, we skip
            if not "DEPRECATED" in _version.stages or _version.time_of_deletion:
                continue

            _time = datetime.now(timezone.utc) + timedelta(days=1, minutes=10)
            _time = _time.strftime("%Y-%m-%dT%H:%M:%SZ")
            _version_details = ScheduleSecretVersionDeletionDetails(
                                                        time_of_deletion=_time)
            try:
                self.__vault.schedule_secret_version_deletion(
                 _version.secret_id, _version.version_number, _version_details)
            except oci.exceptions.ServiceError as e:
                # If there's already the maximum number of secret versions
                # pending deletion, we skip
                if e.status == 400 and e.code == "LimitExceeded":
                    continue
                ebLogWarn("Unable to delete secret version")

    def mCopySecretContent(self, aSecretName: str,
                           aBackupVault: bool = False) -> None:
        """
        Copies the content of a secret from the main vault to the backup vault.

        :param aSecretName: the name of the secret to be copied.
        :param aBackupVault: if True, it will copy the secret from
                             the backup vault to the main vault, insetad.
        """

        _from_vault = self.__vault_id
        _to_vault = self.__backup_vault_id
        _key_id = self.__backup_key_id

        if aBackupVault:
            _from_vault = self.__backup_vault_id
            _to_vault = self.__vault_id
            _key_id = self.__key_id

        # Get content of secret in "from vault"
        _content = self.__secrets_client.get_secret_bundle_by_name(aSecretName,
                                _from_vault).data.secret_bundle_content.content
        _content = json.loads(base64.b64decode(
                                     _content.encode("utf-8")).decode("utf-8"))

        # If no entries in secret, we skip copying it
        if not _content:
            return

        # We check if the secret already exists in the "to vault"
        try:
            _secret = self.__secrets_client.get_secret_bundle_by_name(
                                                   aSecretName, _to_vault).data
        except:
            _secret = None

        # Encode secret content
        _content = base64.b64encode(
                          json.dumps(_content).encode("utf-8")).decode("utf-8")

        _content = Base64SecretContentDetails(content_type="BASE64",
                                              content=_content)

        # We create or update the secret in the "to vault", accordingly
        if _secret:
            _secret_details = UpdateSecretDetails(secret_content=_content)
            self.__vault.update_secret(secret_id=_secret.secret_id,
                                       update_secret_details=_secret_details)
            self.mDeleteSecretVersions(_secret)
        else:
            _secret_details = CreateSecretDetails(key_id=_key_id,
                                          compartment_id=self.__compartment_id,
                                          vault_id=_to_vault,
                                          secret_name=aSecretName,
                                          secret_content=_content)
            _vault = oci.vault.VaultsClientCompositeOperations(self.__vault)
            _vault.create_secret_and_wait_for_state(
              create_secret_details=_secret_details,
              wait_for_states=[oci.vault.models.Secret.LIFECYCLE_STATE_ACTIVE])

        ebLogTrace(f"Copied ExaKms keys content for secret: {aSecretName}")

    def mCleanUpVault(self, aBackupVault: bool = False) -> None:
        """
        Removes all ExaKms entries in the main vault.
        Note: This does not delete the secrets from the vault. It merely
              updates the content of all the secrets to "{}".

        :param aBackupVault: if True, it will remove all entries in
                             the backup vault, instead.
        """

        _secrets = self.mListSecrets(aBackupVault=aBackupVault)

        for _secret in _secrets:
            _encoded_data = json.dumps({}).encode("utf-8")
            _encoded_data = base64.b64encode(_encoded_data).decode("utf-8")
            _secret_content = Base64SecretContentDetails(content_type="BASE64",
                                                         content=_encoded_data)
            _secret_details = UpdateSecretDetails(
                                                secret_content=_secret_content)
            self.__vault.update_secret(secret_id=_secret.id,
                                       update_secret_details=_secret_details)
            self.mDeleteSecretVersions(_secret)
