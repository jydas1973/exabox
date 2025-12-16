#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/fs_encryption/tests_cluencryption.py /main/29 2025/08/08 21:50:09 jfsaldan Exp $
#
# tests_cluencryption.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluencryption.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      This file contains the unittest for the filesystem encryption functions
#
#    NOTES
#    None
#
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    08/05/25 - Bug 38268596 - EXACLOUD FEDRAMP PREVENT PROV
#                           PROBLEM | FS_ENCRYPTION FILE SHREDDING FAILS
#                           CAUSING INSTALL CLUSTERS TO FAIL
#    jfsaldan    04/21/25 - Bug 37856850 - EXACLOUD ENCRYPTION AT REST | ENSURE
#                           CLEANUP OF RESIDUAL FILES IN EXACLOUD IF PREVIOUS
#                           ATTEMPT FAILED
#    jfsaldan    08/26/24 - Bug 36974914 - EXACLOUD - ADD COMPUTE U01
#                           ENCRYPTION FAILS IF AHF IS RUNNING IN U01 FS
#    jfsaldan    07/19/24 - Enh 36776061 - EXACS EXACLOUD OL8 FS ENCRYPTION :
#                           ADD SUPPORT TO RESIZE AN ENCRYPTED U01 DISK
#    jfsaldan    07/03/24 - Enh 36711025 - EXACLOUD OL8 FS ENCRYPTION --
#                           EXACLOUD TO SUPPORT CREATING U01 ENCRYPTED ON THE
#                           DOMU
#    jfsaldan    07/01/24 - Bug 36624871 - EXACS:OL8 ENCRYPTION:23.4.1.2.4:
#                           FILESYSTEM RESIZE FAILING IN INVOKE EXACLOUD FOR
#                           RESHAPE OPERATION
#    ririgoye    06/11/24 - Enh 35761667 - Adding unit tests for passphrase
#                           rotation
#    jfsaldan    05/09/24 - Bug 36427983 - FORTIFY ISSUE: PASSWORD MANAGEMENT:
#                           HARDCODED PASSWORD CLUENCRYPTION.PY
#    jfsaldan    08/22/23 - Bug 35719818 - PLEASE PROVIDE A WAY TO IDENTIFY
#                           FROM A XEN DOM0 IF THE GUESTVM HAS LUKS ENABLED OR
#                           NOT
#    jfsaldan    08/14/23 - Bug 35419066 - EXACS:22.2.1:DROP3:FS ENCRYPTION
#                           ENABLED:KVM PROVISIONING FAILING AT PREVM SETUP
#                           STEP:EXACLOUD : AN ERROR HAS OCCURED WHILE TRYING
#                           TO PUSH A FILESYSTEM ENCRYPTION SECRET KEY
#    jfsaldan    05/23/23 - Bug 35410783 - EXACLOUD FAILED TO CALCULATE THE NON
#    jfsaldan    05/12/23 - Enh 35355004 - EXACLOUD - FS ENCRYPTION - CREATE
#                           DOMU ENCRYPTION PASSPHRASE WITH TAG TO SUPPORT IAM
#                           WITH 1 VAULT
#    jfsaldan    03/08/23 - Bug 35144841 - Delete Node and then add again
#                           issue, keyapi in Dom0 is not overriden with new
#                           values
#    jfsaldan    09/14/22 - Bug 34527636 - XEN - use local passphrase during CS
#                           and rotate to real SiV passphrase later on
#    ndesanto    07/01/22 - OCI connection code consolidation.
#    jfsaldan    05/27/22 - Bug 34219873 - DELETE KEYAPI SHELL WRAPPER FROM
#                           DOM0 DURING DELETE SERVICE
#    jfsaldan    05/18/22 - Enh 34185907 - Add support to use local passphrase
#                           in DEV/QA environments only
#    jfsaldan    05/05/22 - Enh 34082448 - Adding unittest for /u02 encryption
#                           code with OEDA
#    jfsaldan    08/09/21 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from ast import literal_eval
import os
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluencryption import (
    isEncryptionRequested, checkPackages,
    waitForSystemBoot, createLocalFSKey,
    updateFstab, enableSystemdService,
    encryptNode, mountNestedFS, resizeEncryptedVolume,
    prepareExt4FsPrePosEncryption, pushAndReturnNonOedaLocalKeyapi,
    MountPointInfo, getMountPointInfo, pushAndReturnKeyApi,
    parseEncryptionPayload, RemoteOciResources,
    generateObjectData, OCIClients, createOCIClientsSetup,
    createKMSClients, deleteRemotePassphraseSetup,
    createAndPushRemotePassphraseSetup, ensureSystemFirstBootEncryptedExists,
    ensureSystemFirstBootEncryptedExistsParallelSetup, copyOEDAKeyApiToNode,
    useLocalPassphrase, deleteOEDAKeyApiFromDom0, RSAEncryption, SymmetricEncryption,
    deleteEncryptionMarkerFileForVM, createEncryptionMarkerFileForVM,
    resizeOEDAEncryptedFS, setupU01EncryptedDiskPerHost, createEncryptedLVMVmMaker,
    validateMinImgEncryptionSupport, convertGptToMsdosLabelDriver, cleanupU02EncryptedDisk,
    mSetLuksPassphraseOnDom0Exacc)
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import connect_to_host, node_exec_cmd_check, node_cmd_abs_path_check, node_connect_to_host
from exabox.core.Context import get_gcontext
from oci.key_management.models import GeneratedKey
from oci.response import Response
from oci.object_storage import ObjectStorageClient
from oci.secrets import SecretsClient
from oci.vault import VaultsClient, VaultsClientCompositeOperations

PUB_KEY = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDXAonOM3kRgIKgjP1038N2rjMT+YcZgbrPIssyj//yMNFO5mBLugrqhOUjEglZsz+fJBcYfq6sN6gShEMDat8y7vgXYsX5nwsWj6JvOt5dJaLZM0Z/1CRvgiFjZ1bqJhgey3/PuiY7YVCoXPw/YuMLPjh1hQLy4UDmP6mS9jzYZ7u+baHvm9UKcTcCEFlr7c+6+urxeH7PonfMTS9LePf28GqwpKjAvFPyeFnwR81oCgPMBokAOl7ISQadlhTo3mbvqXOqJKArCer+rTZ0TV5MoelgpoAWgva9f/3WM1EYIGqjLCl+Yu+OG83aI5rBg2Ts+iJgWEyLuBxs0/y4CbewXoAasM6WEUFQBNeHeginWIDHESChsRBYuxYSAabw13YpHPCp6QNrFUwhqZkurLise0+6Z8PX2i03mB2gBIZs0JKkOU9NkwBz1f7SAk20PBXb8cu4e6rPrvVEnh8C++0E2hwSnAnaU9mXulcBFFKscexT1Eyell/zdjofDVLwxQM= """
PRIV_KEY = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
NhAAAAAwEAAQAAAYEA1wKJzjN5EYCCoIz9dN/Ddq4zE/mHGYG6zyLLMo//8jDRTuZgS7oK
6oTlIxIJWbM/nyQXGH6urDeoEoRDA2rfMu74F2LF+Z8LFo+ibzreXSWi2TNGf9Qkb4IhY2
dW6iYYHst/z7omO2FQqFz8P2LjCz44dYUC8uFA5j+pkvY82Ge7vm2h75vVCnE3AhBZa+3P
uvrq8Xh+z6J3zE0vS3j39vBqsKSowLxT8nhZ8EfNaAoDzAaJADpeyEkGnZYU6N5m76lzqi
SgKwnq/q02dE1eTKHpYKaAFoL2vX/91jNRGCBqoywpfmLvjhvN2iOawYNk7PoiYFhMi7gc
bNP8uAm3sF6AGrDOlhFBUATXh3oIp1iAxxEgobEQWLsWEgGm8Nd2KRzwqekDaxVMIamZLq
y4rHtPumfD19otN5gdoASGbNCSpDlPTZMAc9X+0gJNtDwV2/HLuHuqz671RJ4fAvvtBNoc
EpwJ2lPZl7pXARRSrHHsU9RMnpZf83Y6Hw1S8MUDAAAFkFkhhOFZIYThAAAAB3NzaC1yc2
EAAAGBANcCic4zeRGAgqCM/XTfw3auMxP5hxmBus8iyzKP//Iw0U7mYEu6CuqE5SMSCVmz
P58kFxh+rqw3qBKEQwNq3zLu+BdixfmfCxaPom863l0lotkzRn/UJG+CIWNnVuomGB7Lf8
+6JjthUKhc/D9i4ws+OHWFAvLhQOY/qZL2PNhnu75toe+b1QpxNwIQWWvtz7r66vF4fs+i
d8xNL0t49/bwarCkqMC8U/J4WfBHzWgKA8wGiQA6XshJBp2WFOjeZu+pc6okoCsJ6v6tNn
RNXkyh6WCmgBaC9r1//dYzURggaqMsKX5i744bzdojmsGDZOz6ImBYTIu4HGzT/LgJt7Be
gBqwzpYRQVAE14d6CKdYgMcRIKGxEFi7FhIBpvDXdikc8KnpA2sVTCGpmS6suKx7T7pnw9
faLTeYHaAEhmzQkqQ5T02TAHPV/tICTbQ8Fdvxy7h7qs+u9USeHwL77QTaHBKcCdpT2Ze6
VwEUUqxx7FPUTJ6WX/N2Oh8NUvDFAwAAAAMBAAEAAAGBALfwIfhXrKE+cYHsXACaVVu4l1
XlSKCXjTsbJv6wlmOZQ9bd20+tbx1GZ8hi68DjSfBZLbD033XRf2Wn5LSNvziRm4hWJcvx
NcktQ+coU4cYZYKvDQbac/k5OFsT0xUpVcUyjrslIwP1ssz2D44iiN3bcu2GxwkFj0HrAK
ULJu5zf/ffToPvqofuZwLK/dUJc4cgldHSJZp4AUi0V1uXt3p4Hq3Tj9KiyqZKM5cNtjnl
J25pwNaDGQb7Aj/aXzUA3TmKvmV0kfoWcS5G8a8A7ic1h3u/SHtoJagh+/xIde7TXiQ6/d
D9gbvXoS6OybbU2G/LS5qf5qP7MTCraGtASm1MfjwMyY8Wn9vOz4geuXWc3bJ/MWdWEWB9
UybGKZ+wubr5KmKCuJsM6M2LJNU3yCLYuRKfddmKjL/cA4G6k5CnAKlebdS2an5xBou8Cr
MTp2O8KEXX8dWGaiShNshlFlx3ob93YTzbC6RexKPFlQczeigSgYk7jvBl3oWS6NeKcQAA
AMEAoXJWUirzisZT3d0LjSfJ09kD6WdbCejthvet5Iw0KFQRlrMG+Dys0fbj0CDViC3yoX
R8gz+1LhZGrWSQoimFsfeF9CDcqvS9vMagWnKYm6E6uqWHOh9x+L/7CseZ0vKu5R2ieTO4
gquZnYA0STsxyIWh6xohwtAocjpRid9Tui9lgcJcby9o12Ms90pvX1G9XbWp6E/TFMOSlJ
j72buroP/YqICPJw36/8UvAB5d+r6RjWl7BcB9uHDicNL4SqgUAAAAwQDrP7WwxCPgSmze
bk9cUCpQ95XgglSaP5pChKDdXzuinxkP9zhLiPkgtt5RoQ7ZbY6hlBGSxEZP1twgR/cytZ
dGALfPP83KRQrGsIE9THe/4U4ti2sSz+HRYqI2rERToR1Ytrlll2q40cUZwLbvsj6UqHb1
ytoL6R1bOhimOCW0YqRH4Uoo1VywJzTJvgX46SsT+oPfukrOkDJJ4iYbLMTt75gPHgZ6cx
3jIErtUzVSeuA5oPWAkQhqn+HVl4SKyDcAAADBAOn5zRiRVe8mtPqqpLHJ/ChurBN3QwGr
yCouyROVXRXU1hxm97Nl2pYnWnEawk7mp6dsjVslbc0wxvh7uZWd9gkKmaxBVdpc0L+Gfl
kW65yZZocW9KPlHUs8IF7nGq5oC+L89lkpibrZpDlg5WLDqPAWASmJ1YvVICQ3EJfNLO+T
VtuKL7P3qNaBlwas0DStvifF1uak8Gv263m6ZSZms0PBM3tYiCdzCUax80ygxjWbnEzYGB
27lyFwpUqTrz8rlQAAABVwYmVsbGFyeUBwYmVsbGFyeS1tYWMBAgME
-----END OPENSSH PRIVATE KEY-----"""

USER_DATA = """__BEGIN__
^M

scaqar05dv0105 login: ^M

scaqar05dv0105 login: ^M

scaqar05dv0105 login: root^M
Password:
Last login: Tue Dec 13 03:56:51 UTC 2022
Last login: Tue Dec 13 03:57:45 on ttyS0
[root@scaqar05dv0105 ~]# pwd
/root
[root@scaqar05dv0105 ~]# exit
[root@scaqar05dv0105 ~]# exit
logout
^M
__END__"""

class ebTestClusterEncryption(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

        self.PATH_ENCRYPTION_JSON_KMS = \
                "exabox/exatest/cluctrl/fs_encryption/resources/fs_encryption_kms.json"
        self.PATH_ENCRYPTION_JSON_SIV = \
                "exabox/exatest/cluctrl/fs_encryption/resources/fs_encryption_siv.json"

        self.PATH_ENCRYPTION_PAYLOAD_KMS = os.path.join(get_gcontext().mGetBasePath()
                , self.PATH_ENCRYPTION_JSON_KMS)
        self.PATH_ENCRYPTION_PAYLOAD_SIV = os.path.join(get_gcontext().mGetBasePath()
                , self.PATH_ENCRYPTION_JSON_SIV)


    #
    # isEncryptionRequested tests
    #

    def test_encryption_not_requested(self):
        """
        This function tests if encryption is requested
        """
        ebLogInfo("Test - Encryption is NOT requested")
        _json = self.mGetPayload()
        self.assertEqual(False, isEncryptionRequested(_json, "domU"))

    def test_encryption_requested(self):
        """
        This function tests if encryption is requested
        """
        ebLogInfo("Test - Encryption IS requested")
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload
        self.assertEqual(True, isEncryptionRequested(_json, "domU"))

    def test_encryption_requested_for_u02(self):
        """
        This function tests if encryption is requested
        """
        ebLogInfo("Test - Encryption IS requested for /u02")

        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload
        self.assertEqual(True, isEncryptionRequested(_json, "domU", "/u02"))

    def test_encryption_not_requested_for_u03(self):
        """
        This function tests if encryption is requested
        """
        ebLogInfo("Test - Encryption IS NOT requested for /u03")
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload
        self.assertEqual(False, isEncryptionRequested(_json, "domU", "/u03"))

    #
    # Test isEncryptionRequested
    #

    #
    # Test encryptNode
    #
    def test_encryptNode_all_good(self):
        """
        Function to test encryptNode
        """

        # Declare commands to run
        _remote_key_api = "/opt/exacloud/fs_encryption/keyapi"
        _remote_config_file = "/opt/exacloud/fs_encryption/config_file"
        _cryptsetup_cmd_reencrypt = ("/sbin/cryptsetup reencrypt "
            "--encrypt /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk "
            "--type luks2 --reduce-device-size 8192S --key-file=-")

        _cryptsetup_cmd_test = ("/sbin/cryptsetup open "
            "--type luks2 --test-passphrase --key-file=- "
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk")

        _cryptsetup_cmd_config = ("/sbin/cryptsetup config "
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk "
            "--label U02_IMAGE-crypt")

        _cryptsetup_cmd_open = ("/sbin/cryptsetup open "
            "--type luks2 --key-file=- "
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk "
            "VGExaDbDisk.u02_extra.img-LVDBDisk-crypt")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand(f"test -e {_remote_key_api}", aRc=1),
                    exaMockCommand(f"test -e {_remote_config_file}", aRc=0),
                    exaMockCommand(f"mkdir -p {os.path.dirname(_remote_key_api)}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} > /dev/null",
                        aRc=0),

                    exaMockCommand(f"scp .* ", aRc=0),

                    exaMockCommand(f"chown root:root", aRc=0),
                    exaMockCommand(f"chmod 500 {_remote_key_api}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} | {_cryptsetup_cmd_reencrypt}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} | {_cryptsetup_cmd_test}", aRc=0),
                    exaMockCommand(f"{_cryptsetup_cmd_config}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} | {_cryptsetup_cmd_open}", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _expected = ["/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt",
                "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"]

        _results = []
        _mount_info = MountPointInfo(
                is_luks = True,
                block_device= "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                fs_type= "ext4",
                fs_label= "U02_IMAGE",
                luks_device= "",
                mount_point= "/u02"
                )

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(encryptNode(_node, _mount_info, _json))

        self.assertEqual(_results, _expected)

    @patch("exabox.ovm.cluencryption.mIsR1")
    def test_encryptNode_all_good_r1_cert_already_present(self, aMagicR1):
        """
        Function to test encryptNode
        """

        # Mock R1 env to test certs command when calling keyapi
        aMagicR1 = True

        # Declare commands to run
        _remote_key_api = "/opt/exacloud/fs_encryption/keyapi"
        _remote_config_file = "/opt/exacloud/fs_encryption/config_file"
        _cryptsetup_cmd_reencrypt = ("/sbin/cryptsetup reencrypt "
            "--encrypt /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk "
            "--type luks2 --reduce-device-size 8192S --key-file=-")

        _cryptsetup_cmd_test = ("/sbin/cryptsetup open "
            "--type luks2 --test-passphrase --key-file=- "
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk")

        _cryptsetup_cmd_config = ("/sbin/cryptsetup config "
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk "
            "--label U02_IMAGE-crypt")

        _cryptsetup_cmd_open = ("/sbin/cryptsetup open "
            "--type luks2 --key-file=- "
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk "
            "VGExaDbDisk.u02_extra.img-LVDBDisk-crypt")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand(f"test -e {_remote_key_api}", aRc=1),
                    exaMockCommand(f"test -e {_remote_config_file}", aRc=0),
                    exaMockCommand(f"mkdir -p {os.path.dirname(_remote_key_api)}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} > /dev/null",
                        aRc=0),

                    exaMockCommand(f"scp .* ", aRc=0),

                    exaMockCommand(f"chown root:root", aRc=0),
                    exaMockCommand(f"chmod 500 {_remote_key_api}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} | {_cryptsetup_cmd_reencrypt}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} | {_cryptsetup_cmd_test}", aRc=0),
                    exaMockCommand(f"{_cryptsetup_cmd_config}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} | {_cryptsetup_cmd_open}", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables to use
        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _expected = ["/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt",
                "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"]

        _results = []
        _mount_info = MountPointInfo(
                is_luks = True,
                block_device= "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                fs_type= "ext4",
                fs_label= "U02_IMAGE",
                luks_device= "",
                mount_point= "/u02"
                )

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(encryptNode(_node, _mount_info, _json))

        self.assertEqual(_results, _expected)
    #
    # Test encryptNode
    #

    #
    # Test mountNestedFS
    #

    def test_mountNestedFS_all_mounted_ok(self):
        """
        Test mountNestedFS
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),
                    exaMockCommand('grep "/u02" /etc/fstab -c', aRc=0, aStdout="1\n"),
                    exaMockCommand('mount -av', aRc=0),

                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = [None, None]
        _results = []

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(mountNestedFS(_node, "/u02"))

        self.assertEqual(_results, _expected)

    #
    # Test mountNestedFS
    #

    #
    # Test updateFstab
    #

    def test_updateFstab_update_ok(self):
        """
        Testing function updateFstab
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),
                    exaMockCommand('grep "/u02" /etc/fstab',
                        aRc=0,
                        aStdout="/dev/VGExaDbDisk.u02_extra.img/LVDBDisk /u02 ext4 defaults 1 1\n"),
                    exaMockCommand('sed -E -i.*', aRc=0),
                    exaMockCommand('cat /etc/fstab', aRc=0),
                    exaMockCommand('mount -fva', aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = [None, None]
        _results = []

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(updateFstab(_node, "/u02",
                    "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"))

        self.assertEqual(_results, _expected)

    def test_updateFstab_update_already_has_netdev(self):
        """
        Testing function updateFstab
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),
                    exaMockCommand('grep "/u02" /etc/fstab',
                        aRc=0,
                        aStdout="/dev/VGExaDbDisk.u02_extra.img/LVDBDisk /u02 ext4 defaults_netdev 1 1\n"),
                    exaMockCommand('sed -E -i.*', aRc=0),
                    exaMockCommand('cat /etc/fstab', aRc=0),
                    exaMockCommand('mount -fva', aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = [None, None]
        _results = []

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(updateFstab(_node, "/u02",
                    "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"))

        self.assertEqual(_results, _expected)

    def test_updateFstab_fstab_invalid_format(self):
        """
        Testing function updateFstab
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),
                    exaMockCommand('grep "/u02" /etc/fstab',
                        aRc=0,
                        aStdout="/dev/VGExaDbDisk.u02_extra.img/LVDBDisk /u02 defaults_netdev 1 1\n"),
                    exaMockCommand('sed -E -i.*', aRc=0),
                    exaMockCommand('cat /etc/fstab', aRc=0),
                    exaMockCommand('mount -fva', aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)


        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                self.assertRaises(ExacloudRuntimeError,
                    lambda: updateFstab(_node, "/u02",
                    "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"))

    #
    # Test updateFstab
    #

    #
    # Test enableSystemdService
    #

    def test_enableSystemdService_copy_and_enable(self):
        """
        Function to test enableSystemdService
        """

        _mountpoint = "/u02"
        _service = "luks-dev-u02.service"
        _service_unit_file = f"/etc/systemd/system/{_service}"
        _keyapi = "/opt/exacloud/fs_encryption/keyapi"
        _config_file = "/opt/exacloud/fs_encryption/config_file"
        _luks_mapper = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"
        _luks_device = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"


        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    # get commands
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),

                    exaMockCommand("test -e /sbin/*", aRc=0, aPersist=True),

                     # check if service already exists
                    exaMockCommand(f"test -e {_service_unit_file}", aRc=0),

                    # check if service already active
                    exaMockCommand(f"systemctl is-active {_service}", aRc=1),

                    # check if mount unit file is calculated correctly
                    exaMockCommand("systemctl is-active u02.mount", aRc=0),

                    # check keyapi exists
                    exaMockCommand(f"test -e {_keyapi}", aRc=0),

                    # check config file exists
                    exaMockCommand(f"test -e {_config_file}", aRc=0),

                    # check keyapi works
                    exaMockCommand(f"keyapi fetch -i {_config_file} > /dev/null", aRc=0),

                    # get fs info
                    exaMockCommand(f"findmnt -rno source,fstype,label /u02",
                        aRc=0,
                        aStdout=f"{_luks_mapper} ext4 U02_IMAGE\n"),

                    # get volume type
                    exaMockCommand(f"lsblk -rno TYPE {_luks_mapper}",
                        aRc=0,
                        aStdout="crypt\n"),

                    # get luks device
                    exaMockCommand(f"lsblk -nprso NAME {_luks_mapper}",
                        aRc=0,
                        aStdout = (f"{_luks_mapper}\n"
                            f"{_luks_device}\n"
                            "/dev/sdb1\n"
                            "/dev/sdb\n")),

                    # get mountpoint
                    exaMockCommand("findmnt -rno target .*",
                        aRc=0,
                        aStdout="/u02\n"),

                    # cp service unit file
                    exaMockCommand(f"/bin/scp", aRc=0),

                    # ownership
                    exaMockCommand(f"chown root:root {_service_unit_file}", aRc=0),

                    # permission
                    exaMockCommand(f"chmod 600 {_service_unit_file}", aRc=0),

                    # enable service
                    exaMockCommand(f"systemctl enable {_service}", aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = [None, None]
        _results = []

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                    _results.append(enableSystemdService(_node, "/u02"))

        self.assertEqual(_results, _expected)

    @patch("exabox.ovm.cluencryption.mIsR1")
    def test_enableSystemdService_copy_and_enable_r1_certs(self, aMagicR1):
        """
        Function to test enableSystemdService
        """

        # Mock R1 env
        aMagicR1 = True
        _mountpoint = "/u02"
        _service = "luks-dev-u02.service"
        _service_unit_file = f"/etc/systemd/system/{_service}"
        _keyapi = "/opt/exacloud/fs_encryption/keyapi"
        _config_file = "/opt/exacloud/fs_encryption/config_file"
        _certs_file = "/opt/exacloud/fs_encryption/certs_file"
        _luks_mapper = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"
        _luks_device = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"


        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    # get commands
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),

                    exaMockCommand("test -e /sbin/*", aRc=0, aPersist=True),

                     # check if service already exists
                    exaMockCommand(f"test -e {_service_unit_file}", aRc=0),

                    # check if service already active
                    exaMockCommand(f"systemctl is-active {_service}", aRc=1),

                    # check if mount unit file is calculated correctly
                    exaMockCommand("systemctl is-active u02.mount", aRc=0),

                    # check keyapi exists
                    exaMockCommand(f"test -e {_keyapi}", aRc=0),

                    # check config file exists
                    exaMockCommand(f"test -e {_config_file}", aRc=0),

                    # check certs file exists
                    exaMockCommand(f"test -e {_certs_file}", aRc=0),

                    # check keyapi works
                    exaMockCommand(f"keyapi fetch -i {_config_file} > /dev/null", aRc=0),

                    # get fs info
                    exaMockCommand(f"findmnt -rno source,fstype,label /u02",
                        aRc=0,
                        aStdout=f"{_luks_mapper} ext4 U02_IMAGE\n"),

                    # get volume type
                    exaMockCommand(f"lsblk -rno TYPE {_luks_mapper}",
                        aRc=0,
                        aStdout="crypt\n"),

                    # get luks device
                    exaMockCommand(f"lsblk -nprso NAME {_luks_mapper}",
                        aRc=0,
                        aStdout = (f"{_luks_mapper}\n"
                            f"{_luks_device}\n"
                            "/dev/sdb1\n"
                            "/dev/sdb\n")),

                    # get mountpoint
                    exaMockCommand("findmnt -rno target .*",
                        aRc=0,
                        aStdout="/u02\n"),

                    # cp service unit file
                    exaMockCommand(f"/bin/scp", aRc=0),

                    # ownership
                    exaMockCommand(f"chown root:root {_service_unit_file}", aRc=0),

                    # permission
                    exaMockCommand(f"chmod 600 {_service_unit_file}", aRc=0),

                    # enable service
                    exaMockCommand(f"systemctl enable {_service}", aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected = [None, None]
        _results = []

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                    _results.append(enableSystemdService(_node, "/u02"))

        self.assertEqual(_results, _expected)
    #
    # Test enableSystemdService
    #

    #
    # Test checkPackages
    #
    def test_checkPackages_present(self):
        """
        Function to test checkPackages
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),
                    exaMockCommand("rpm -q cryptsetup", aRc=0,
                        aStdout="cryptsetup-2.3.0-1.0.1.el7.x86_64\n"),

                    exaMockCommand("rpm -q cryptsetup-libs", aRc=0,
                        aStdout="cryptsetup-libs-2.3.0-1.0.1.el7.x86_64\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _expected = [None, None]
        _results = []
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(checkPackages(_node))

        self.assertEqual(_results, _expected)

    def test_checkPackages_not_install_present_no_install(self):
        """
        Function to test checkPackages
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/*", aRc=0, aPersist=True),
                    exaMockCommand("rpm -q cryptsetup", aRc=0,
                        aStdout=""),

                    exaMockCommand("rpm -q cryptsetup-libs", aRc=0,
                        aStdout=""),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _expected = [None, None]
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                self.assertRaises(ExacloudRuntimeError, lambda : checkPackages(_node))

    #
    # Test checkPackages
    #

    #
    # Test waitForSystemBoot
    #

    def test_waitForSystemBoot_already_boot(self):
        """
        Function to test waitForSystemBoot
        """

        # Prepare cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /*", aRc=0, aPersist=True),
                    exaMockCommand("systemd-analyze time", aRc=0)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _expected = [None, None]
        _results = []
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _results.append(waitForSystemBoot(_node))

        self.assertEqual(_results, _expected)

    #
    # Test waitForSystemBoot
    #

    #
    # Test getMountPointInfo
    #

    def template_test_getMountPointInfo(self, aRC: dict, aOut:dict, aData:dict):
        """
        Function to stress getMountPointInfo

        :param aRc: Dictionary containing return codes to use on MockCommands
        :param aOut: Dictionary containing useful stdout of commands to use
        :param aData: Dictionary containing useful information for the test
        """

        # Declara variables
        _mountpoint = aData.get("mountpoint")
        _device = aOut.get("findmnt_source").strip()

        # Mock cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/.*", aRc=0, aPersist=True),
                    exaMockCommand("findmnt -rno source,fstype,label .*",
                        aRc=aRC.get("findmnt"),
                        aStdout=aOut.get("findmnt")),

                    exaMockCommand(f"lsblk -rno TYPE {_device}",
                        aRc=aRC.get("lsblk_type"),
                        aStdout=aOut.get("lsblk_type")),

                    exaMockCommand(f"lsblk -nprso NAME {_device}",
                        aRc=aRC.get("lsblk_name"),
                        aStdout=aOut.get("lsblk_name")),

                    exaMockCommand("findmnt -rno target .*",
                        aRc=aRC.get("findmnt"),
                        aStdout=aData.get("mountpoint")),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _mount_info_dict = []
        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _mount_info_dict.append(getMountPointInfo(_node, _mountpoint))

        return _mount_info_dict

    def test_getMountPointInfo_u02_not_encrypted(self):
        """
        """

        # Return code dictionary
        _rc = {}
        _rc["findmnt"] = 0
        _rc["lsblk_type"] = 0
        _rc["lsblk_name"] = 0

        # stdout dictionary
        _stdout = {}
        _stdout["findmnt"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk ext4 U02_IMAGE\n"
        _stdout["findmnt_source"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk\n"
        _stdout["findmnt_label"] = "U02_IMAGE\n"
        _stdout["findmnt_fstype"] = "ext4\n"
        _stdout["lsblk_type"] = "lvm\n"

        # additional data dictionary
        _data = {}
        _data["mountpoint"] = "/u02"

        # Build expected result
        _is_luks = False
        _luks_device = ""
        _expected = MountPointInfo(_is_luks, _stdout.get("findmnt_source").strip(),
                _stdout.get("findmnt_fstype").strip(),
                _stdout.get("findmnt_label").strip(),
                _luks_device, _data["mountpoint"])

        self.assertEqual([_expected, _expected],
                self.template_test_getMountPointInfo(_rc, _stdout, _data))

    def test_getMountPointInfo_u02_encrypted(self):
        """
        """

        # Return code dictionary
        _rc = {}
        _rc["findmnt"] = 0
        _rc["lsblk_type"] = 0
        _rc["lsblk_name"] = 0

        # stdout dictionary
        _stdout = {}
        _stdout["findmnt"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt ext4 U02_IMAGE\n"
        _stdout["findmnt_source"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
        _stdout["findmnt_label"] = "U02_IMAGE\n"
        _stdout["findmnt_fstype"] = "ext4\n"
        _stdout["lsblk_type"] = "crypt\n"
        _stdout["lsblk_name"] = ("/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk\n"
            "/dev/sdb1\n"
            "/dev/sdb\n")

        # additional data dictionary
        _data = {}
        _data["mountpoint"] = "/u02"

        # Build expected result
        _is_luks = True
        _luks_device = _stdout.get("findmnt_source").strip().strip('-crypt')
        _expected = MountPointInfo(_is_luks, _stdout.get("findmnt_source").strip(),
                _stdout.get("findmnt_fstype").strip(),
                _stdout.get("findmnt_label").strip(),
                _luks_device, _data["mountpoint"])

        self.assertEqual([_expected, _expected],
                self.template_test_getMountPointInfo(_rc, _stdout, _data))

    #
    # Test getMountPointInfo
    #

    #
    # Test prepareExt4FsPrePosEncryption
    #

    def template_test_prepareExt4FsPrePosEncryption(self, aRC: dict, aDevice: str,
            aPreEncryption: bool):
        """
        Template function to stress prepareExt4FsPrePosEncryption function

        :param aRC: a dictionary with return codes for exaMockCommands
        :param aDevice: the device on which to apply the commands to prepare ext4 fs
        :param aPreEncryptoin: True if steps are pre encryption, False is steps to
            perform are post encryption
        """

        # Mock cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand(f"e2fsck -f -p {aDevice}", aRc=0),
                    exaMockCommand(f"resize2fs -M {aDevice}", aRc=0),
                    exaMockCommand(f"resize2fs {aDevice}", aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                prepareExt4FsPrePosEncryption(_node, aDevice, aPreEncryption)

    def test_prepareExt4FsPrePosEncryption_pre_encryption(self):
        """
        """

        # return code dict
        _rc = {}
        _rc["e2fsck"] = 0

        _device = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"

        self.template_test_prepareExt4FsPrePosEncryption(_rc, _device, True)

    def test_prepareExt4FsPrePosEncryption_post_encryption(self):
        """
        """

        # return code dict
        _rc = {}
        _rc["e2fsck"] = 0

        _device = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"

        self.template_test_prepareExt4FsPrePosEncryption(_rc, _device, False)

    #
    # Test prepareExt4FsPrePosEncryption
    #

    #
    # Test resizeEncryptedVolume
    #

    def template_test_resizeEncryptedVolume(self, aRC:dict, aOut:dict):
        """
        Templtate to stress functions resizeEncryptedVolume
        """

        _device = aOut.get("findmnt_source").strip()
        _keyapi = "/opt/exacloud/keyapi"
        _config_file = "/opt/exacloud/config_file"

        # Mock cmds
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand("findmnt -rno source,fstype,label .*", aRc=aRC.get("findmnt"), aStdout=aOut.get("findmnt")),
                    exaMockCommand("findmnt -rno target .*", aRc=aRC.get("findmnt"), aStdout="/u02\n"),
                    exaMockCommand(f"lsblk -rno TYPE {_device}", aRc=aRC.get("lsblk_type"), aStdout=aOut.get("lsblk_type")),
                    exaMockCommand(f"lsblk -nprso NAME {_device}", aRc=aRC.get("lsblk_name"), aStdout=aOut.get("lsblk_name")),
                    #exaMockCommand(f"mkdir -p /opt/exacloud", aRc=0),
                    #exaMockCommand(f"/bin/scp packages/keyapi {_keyapi}", aRc=0),
                    #exaMockCommand(f"chown root:root {_keyapi}", aRc=0),
                    #exaMockCommand(f"chmod 500 {_keyapi}", aRc=0),
                    exaMockCommand(f"{_keyapi} fetch -i {_config_file} > /dev/null", aRc=aRC.get("keyapi")),
                    exaMockCommand(f"cryptsetup resize {_device} --key-file=.*", aRc=aRC.get("cryptsetup_resize")),
                    exaMockCommand(f"xfs_growfs .*", aRc=aRC.get("xfs_growfs")),
                    exaMockCommand(f"resize2fs .*", aRc=aRC.get("resize2fs")),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            resizeEncryptedVolume(_domU, "/u02")

    def test_resizeEncryptedVolume_encrypted_ext4(self):

        # Return code dictionary
        _rc = {}
        _rc["findmnt"] = 0
        _rc["lsblk_type"] = 0
        _rc["lsblk_name"] = 0
        _rc["cryptsetup_resize"] = 0
        _rc["resize2fs"] = 0
        _rc["keyapi"] = 0

        # stdout dictionary
        _stdout = {}
        _stdout["findmnt"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt ext4 U02_IMAGE\n"
        _stdout["findmnt_source"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
        _stdout["lsblk_type"] = "crypt\n"
        _stdout["lsblk_name"] = ("/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk\n"
            "/dev/sdb1\n"
            "/dev/sdb\n")

        self.assertEqual(None, self.template_test_resizeEncryptedVolume(_rc, _stdout))

    def test_resizeEncryptedVolume_not_encrypted_ext4(self):

        # Return code dictionary
        _rc = {}
        _rc["findmnt"] = 0
        _rc["lsblk_type"] = 0
        _rc["lsblk_name"] = 0
        _rc["cryptsetup_resize"] = 0
        _rc["xfs_growfs"] = 0
        _rc["resize2fs"] = 0
        _rc["keyapi"] = 0

        # stdout dictionary
        _stdout = {}
        _stdout["findmnt"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt ext4 U02_IMAGE\n"
        _stdout["findmnt_source"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
        _stdout["lsblk_type"] = "lvm\n"
        _stdout["lsblk_name"] = ("/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk\n"
            "/dev/sdb1\n"
            "/dev/sdb\n")

        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_resizeEncryptedVolume(_rc, _stdout))

    def test_resizeEncryptedVolume_encrypted_xfs(self):

        # Return code dictionary
        _rc = {}
        _rc["findmnt"] = 0
        _rc["lsblk_type"] = 0
        _rc["lsblk_name"] = 0
        _rc["cryptsetup_resize"] = 0
        _rc["xfs_growfs"] = 0
        _rc["resize2fs"] = 0
        _rc["keyapi"] = 0

        # stdout dictionary
        _stdout = {}
        _stdout["findmnt"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt ext4 U02_IMAGE\n"
        _stdout["findmnt_source"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
        _stdout["lsblk_type"] = "crypt\n"
        _stdout["lsblk_name"] = ("/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk\n"
            "/dev/sdb1\n"
            "/dev/sdb\n")

        self.assertEqual(None, self.template_test_resizeEncryptedVolume(_rc, _stdout))

    @patch("exabox.ovm.cluencryption.mIsR1")
    def test_resizeEncryptedVolume_encrypted_ext4_r1_certs_already_present(
            self, aMagicR1):

        aMagicR1 = True

        # Return code dictionary
        _rc = {}
        _rc["findmnt"] = 0
        _rc["lsblk_type"] = 0
        _rc["lsblk_name"] = 0
        _rc["cryptsetup_resize"] = 0
        _rc["resize2fs"] = 0
        _rc["keyapi"] = 0

        # stdout dictionary
        _stdout = {}
        _stdout["findmnt"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt ext4 U02_IMAGE\n"
        _stdout["findmnt_source"] = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
        _stdout["lsblk_type"] = "crypt\n"
        _stdout["lsblk_name"] = ("/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt\n"
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk\n"
            "/dev/sdb1\n"
            "/dev/sdb\n")

        self.assertEqual(None, self.template_test_resizeEncryptedVolume(_rc, _stdout))

    #
    # Test resizeEncryptedVolume
    #


    #
    # Test resizeOEDAEncryptedFS
    #

    def test_resizeOEDAEncryptedFS(self):
        """
        Test resizeOEDAEncryptedFS
        """

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test.*lsblk", aRc=0),
                    exaMockCommand("test.*findmnt", aRc=0),
                    exaMockCommand("findmnt -rno target /u01",
                        aRc=0,
                        aStdout="/u01\n"),
                    exaMockCommand("/bin/findmnt -rno source,fstype,label /u01", aRc=0,
                        aStdout="/dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk-crypt xfs\n"),
                    exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk-crypt", aRc=0,
                        aStdout="crypt\n"),
                    exaMockCommand("/bin/lsblk -nprso NAME /dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk-crypt", aRc=0,
                        aStdout=(
                            "/dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk-crypt\n"
                            "/dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk\n"
                            "/dev/sdd1\n"
                            "/dev/sdd\n")),
                    exaMockCommand("/bin/test -e.*key-api.sh", aRc=0),
                    exaMockCommand("/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh",
                        aRc=0, aStdout="/tmp/fs_encryption_keyapi"),
                    exaMockCommand("test.*cryptsetup", aRc=0),
                    exaMockCommand("cryptsetup resize.*", aRc=0),
                    exaMockCommand("test.*xfs", aRc=0),
                    exaMockCommand("xfs_growfs /u01", aRc=0),
                    exaMockCommand("test -e /tmp/fs_encryption_keyapi", aRc=0),
                    exaMockCommand("rm -f /tmp/fs_encryption_keyapi", aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        for _, _domU in ebox.mReturnDom0DomUPair():
            self.assertEqual(None, resizeOEDAEncryptedFS(ebox, _domU, "/u01"))
    #
    # Test resizeOEDAEncryptedFS
    #

    #
    # Test pushAndReturnKeyApi
    #

    def template_test_pushAndReturnKeyApi(self):
        """
        Function to test pushAndReturnKeyApi
        """

        _remote_key_api = "/opt/exacloud/fs_encryption/keyapi"
        _remote_key_file_local_keyapi = "/etc/fs_crypt_key"
        _remote_config_file = "/opt/exacloud/fs_encryption/config_file"
        _remote_certs_file = "/opt/exacloud/fs_encryption/certs_file"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/.*", aRc=0, aPersist=True),
                    exaMockCommand(f"test -e {_remote_key_api}", aRc=1),
                    exaMockCommand(f"test -e {_remote_config_file}", aRc=0),
                    exaMockCommand(f"test -e {_remote_certs_file}", aRc=0),
                    exaMockCommand(f"mkdir -p {os.path.dirname(_remote_key_api)}", aRc=0),

                    exaMockCommand(f"/bin/scp exabox/kms/combined_r1.crt {_remote_certs_file}"),
                    exaMockCommand(f"/bin/chown root:root {_remote_certs_file}"),
                    exaMockCommand(f"/bin/chmod 500 {_remote_certs_file}"),
                    exaMockCommand(f"/bin/scp packages/keyapi {_remote_key_api}"),
                    exaMockCommand(f"/bin/scp /tmp/.* {_remote_config_file}"),
                    exaMockCommand(f"/bin/chown root:root {_remote_config_file}"),
                    exaMockCommand(f"/bin/chmod 500 {_remote_config_file}"),

                    exaMockCommand(f"chown root:root", aRc=0),
                    exaMockCommand(f"chmod 500 {_remote_key_api}", aRc=0),

                    # Bef
                    exaMockCommand(f"test -e {_remote_key_file_local_keyapi}", aRc=0),
                    exaMockCommand(f"test -e {_remote_key_api}", aRc=1),
                    exaMockCommand(f"test -e {_remote_config_file}", aRc=0),
                    exaMockCommand(f"test -e {_remote_certs_file}", aRc=0),
                    exaMockCommand(f"mkdir -p {os.path.dirname(_remote_key_api)}", aRc=0),

                    exaMockCommand(f"/bin/scp exabox/kms/combined_r1.crt {_remote_certs_file}"),
                    exaMockCommand(f"/bin/chown root:root {_remote_certs_file}"),
                    exaMockCommand(f"/bin/chmod 500 {_remote_certs_file}"),
                    exaMockCommand(f"/bin/scp .* {_remote_key_api}"),
                    exaMockCommand(f"/bin/scp /tmp/.* {_remote_config_file}"),
                    exaMockCommand(f"/bin/chown root:root {_remote_config_file}"),
                    exaMockCommand(f"/bin/chmod 500 {_remote_config_file}"),

                    exaMockCommand(f"chown root:root", aRc=0),
                    exaMockCommand(f"chmod 500 {_remote_key_api}", aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _return_values = []
        _options = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _options.jsonconf["fs_encryption"] = _enc_payload

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _return_values.append(pushAndReturnKeyApi(_node, _domU))

        return _return_values

    def test_pushAndReturnKeyApi_keyapiNotPresent_no_certs(self):
        """
        Test pushAndReturnKeyApi when KeyAPi is not already present in the system
        """

        _expected_results = ("/opt/exacloud/fs_encryption/keyapi", "/opt/exacloud/fs_encryption/config_file", "")
        self.assertEqual([_expected_results, _expected_results],  self.template_test_pushAndReturnKeyApi())

    @patch("exabox.ovm.cluencryption.mIsR1")
    def test_pushAndReturnKeyApi_keyapiNotPresent_r1_certs_already_present(self, aMagicR1):
        """
        Test pushAndReturnKeyApi when KeyAPi is not already present in the system
        """

        # Mock r1 environment
        aMagicR1 = True
        _expected_results = ("/opt/exacloud/fs_encryption/keyapi", "/opt/exacloud/fs_encryption/config_file", "/opt/exacloud/fs_encryption/certs_file")
        self.assertEqual([_expected_results, _expected_results],  self.template_test_pushAndReturnKeyApi())

    #
    # Test pushAndReturnKeyApi
    #

    #
    # Test pushAndReturnNonOedaLocalKeyapi
    #

    def test_pushAndReturnNonOedaLocalKeyApi(self):
        """
        Function to test pushAndReturnKeyApi
        """

        _remote_key_api = "/opt/exacloud/fs_encryption/keyapi"
        _remote_config_file = "/opt/exacloud/fs_encryption/config_file"
        _remote_key_file = "/etc/fs_crypt_key"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e /bin/.*", aRc=0, aPersist=True),
                    exaMockCommand(f"test -e {_remote_key_api}", aRc=1),
                    exaMockCommand(f"test -e {_remote_config_file}", aRc=0),
                    exaMockCommand(f"test -e {_remote_key_file}", aRc=0),
                    exaMockCommand(f"mkdir -p {os.path.dirname(_remote_key_api)}", aRc=0),

                    exaMockCommand(f"scp .* ", aRc=0),

                    exaMockCommand(f"chown root:root", aRc=0),
                    exaMockCommand(f"chmod 500 {_remote_key_api}", aRc=0),
                    exaMockCommand(f"{_remote_key_api} fetch -i {_remote_config_file} > /dev/null", aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _return_values = []

        # On local keyapi we dont need the config_file nor certs
        _expected = ("/opt/exacloud/fs_encryption/keyapi", "", "")

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:

                self.assertRaises(Exception,
                    lambda: pushAndReturnNonOedaLocalKeyapi(_node))

    #
    # Test pushAndReturnNonOedaLocalKeyapi
    #

    #
    # Test parseEncryptionPayload
    #

    def test_parseEncryptionPayload_all_good(self):
        """
        This function tests the parsing of the payload
        """
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload

        # Fill all expected fields
        _expected = RemoteOciResources(
            _enc_payload.get("kms_id"),
            _enc_payload.get("kms_key_endpoint"),
            _enc_payload.get("bucket_name"),
            _enc_payload.get("bucket_namespace"),
            _enc_payload.get("vault_id"),
            _enc_payload.get("secret_compartment_id"),
            "SIV",
            _enc_payload.get("cloud_vmcluster_id"),
        )

        self.assertEqual(_expected, parseEncryptionPayload(_json, "domU"))

    #
    # Test parseEncryptionPayload
    #

    #
    # Test generateObjectData
    #

    def test_generateObjectData(self):
        """
        Function to test Generate Object data, since a random
        password is generated here, we cannot check for exact result
        of test_generateObjectData, but we check for return
        output format
        """

        # Declare known dummy ciphertext and plaintext
        _ciphertext = ("ISuqxx/lLOc+AKO457nmrBLblwdokri/+3oG1dVy1Dq2LyfEcWYYKSUk"
                "hmXd1AngmalwGOsNJbwE/WuQ0AHCfDCisxMo5wAAAAA=")
        _plaintext = ("3hQjtCBZdC0iPuR4N/cmoUIOW/uBs/r78SbEMEBzBj4=")

        _json_enc_data = generateObjectData(_ciphertext, _plaintext)
        _returned_dict = literal_eval(_json_enc_data)

        self.assertEqual(_ciphertext, _returned_dict.get("encDEK"))
        self.assertTrue(isinstance(_json_enc_data, str))
        self.assertTrue(isinstance(_returned_dict.get("encData", None), str))
        self.assertTrue(len(_returned_dict)==2)

    #
    # Test generateObjectData
    #

    #
    # Test createKMSClients
    #

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.exaoci.ExaOCIFactory.KmsCryptoClient")
    @patch("exabox.exaoci.ExaOCIFactory.ObjectStorageClient")
    @patch("exabox.ovm.cluencryption.ExaOCIFactory")
    def test_createKMSClients_commercial_region(self,
            aExaOCIFactory, aMagicMockObjectStorageClient,
            aMagicMockKmsCryptoClient, aMagicR1):
        """
        This method tests the createKMSClients function
        We patch the InstancePrincipal, ObjectStorageClient and KMSCryptoClient with
        Magic Mock mode to simulate that the creation is successful
        """

        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Modify aMagicR1 to make it return False so that we can test creation of signers
        # as if we were not in R1
        aMagicR1.return_value = False

        aExaOCIFactory.return_value.get_object_storage_client.return_value = aMagicMockObjectStorageClient
        aExaOCIFactory.return_value.get_crypto_client.return_value = aMagicMockKmsCryptoClient

        # Attempt to initialize the required OCI Client
        _oci_clients = createKMSClients(
                aKMSCryptoEndpoint = _remote_oci_resources.kms_crypto_endpoint,
                aKMSKeyId = _remote_oci_resources.kms_ocid)
        self.assertIsInstance(_oci_clients, OCIClients)
        self.assertTrue( _oci_clients.secrets_client == None)
        self.assertTrue( _oci_clients.vault_client == None)

    @patch("exabox.ovm.cluencryption.urlopen")
    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.exaoci.ExaOCIFactory.KmsCryptoClient")
    @patch("exabox.exaoci.ExaOCIFactory.ObjectStorageClient")
    @patch("exabox.exaoci.ExaOCIFactory.ExaboxConfConnector")
    @patch("exabox.ovm.cluencryption.ExaOCIFactory")
    def test_createOCIClients_non_commercial_region(self,
            aExaOCIFactory, aExaboxConfConnector, 
            aMagicMockObjectStorageClient, aMagicMockKmsCryptoClient, 
            aMagicR1, aUrlOpen):
        """
        This method tests the createKMSClients function
        """
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload

        # Set the below two config variable to mock we are in a special region e.g. gov
        self.mGetContext().mSetConfigOption("oci_certificate_path", "/some/path")
        self.mGetContext().mSetConfigOption("oci_service_domain", "some_domain")

        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Modify aMagicR1 to make it return False so that we can test creation of signers
        # as if we were not in R1
        aMagicR1.return_value = False

        # Modify urlopen call to mock a valid region
        aUrlOpen.return_value.read.return_value = "sea"

        # Create an ExaOCIFactory with an ExaboxConfConnector connector
        aExaOCIFactory.return_value.get_oci_connector.return_value = aExaboxConfConnector
        aExaOCIFactory.return_value.get_object_storage_client.return_value = aMagicMockObjectStorageClient
        aExaOCIFactory.return_value.get_crypto_client.return_value = aMagicMockKmsCryptoClient

        # Attempt to initialize the required OCI Client
        _oci_clients = createKMSClients(
                aKMSCryptoEndpoint = _remote_oci_resources.kms_crypto_endpoint,
                aKMSKeyId = _remote_oci_resources.kms_ocid)
        self.assertIsInstance(_oci_clients, OCIClients)
        self.assertTrue( _oci_clients.secrets_client == None)
        self.assertTrue( _oci_clients.vault_client == None)

        # Delete values from context
        self.mGetContext().mSetConfigOption("oci_certificate_path", None)
        self.mGetContext().mSetConfigOption("oci_service_domain", None)

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.ovm.cluencryption.ExaOCIFactory")
    def test_createOCIClients_commercial_region_error(self,
            aExaOCIFactory, aMagicR1):
        """
        This method tests the createKMSClients function
        """
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Modify aMagicR1 to make it return False so that we can test creation of signers
        # as if we were not in R1
        aMagicR1.return_value = False

        # Modify aExaOCIFactory to make it fail
        # It doesnt matter which exception we assign to side_effect since in cluencryption
        # exacloud catches all exception types
        aExaOCIFactory.side_effect = Exception("Unable to create")

        # createKMSClients should raise an exception if unable to create the signer
        self.assertRaises(Exception,
                lambda: createKMSClients(
                    aKMSCryptoEndpoint = _remote_oci_resources.kms_crypto_endpoint,
                    aKMSKeyId = _remote_oci_resources.kms_ocid))

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.exaoci.ExaOCIFactory.KmsCryptoClient")
    @patch("exabox.exaoci.ExaOCIFactory.ObjectStorageClient")
    @patch("exabox.ovm.cluencryption.ExaOCIFactory")
    def test_createOCIClients_r1(self,
            aExaOCIFactory, aMagicMockObjectStorageClient,
            aMagicMockKmsCryptoClient, aMagicR1):
        """
        This method tests the createKMSClients function
        We patch the InstancePrincipal, ObjectStorageClient and KMSCryptoClient with
        Magic Mock mode to simulate that the creation is successful
        """

        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_KMS)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Modify aMagicR1 to make it return True so that we can test creation of signers
        # as if we were in R1
        aMagicR1.return_value = True

        # Perform test
        _oci_clients = createKMSClients(
                aKMSCryptoEndpoint = _remote_oci_resources.kms_crypto_endpoint,
                aKMSKeyId = _remote_oci_resources.kms_ocid)
        self.assertIsInstance(_oci_clients, OCIClients)
        self.assertTrue( _oci_clients.secrets_client == None)
        self.assertTrue( _oci_clients.vault_client == None)

    #
    # Test createKMSClients
    #

    #
    # Test createVaultClients
    #
    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.ovm.cluencryption.createVaultClients", create=OCIClients)
    @patch("exabox.exaoci.ExaOCIFactory")
    def test_createVaultClients_commercial_region_ok(self,
            aExaOCIFactory, aOCIClients, aMagicR1):
        """
        Function to test checkRemotePassphraseNotPresentSiV
        """
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Modify aMagicR1 to make it return True so that we can test creation of signers
        # as if we were in R1
        aMagicR1.return_value = False

        aOCIClients = OCIClients(
            object_storage_client = None,
            kms_crypto_client = None,
            generate_key_details = None,
            vault_client = None,
            secrets_client = None)

        # Perform test
        _oci_clients = aOCIClients
        self.assertIsInstance(_oci_clients, OCIClients)
        self.assertIsNone(_oci_clients.kms_crypto_client)
        self.assertIsNone(_oci_clients.generate_key_details)

    @patch("exabox.ovm.cluencryption.mIsR1")
    def test_createVaultClients_r1_ok(self,
            aMagicR1):
        """
        Function to test checkRemotePassphraseNotPresentSiV
        """
        # Modify aMagicR1 to make it return True so that we can test creation of signers
        # as if we were in R1
        aMagicR1.return_value = True

        aOCIClients = OCIClients(
            object_storage_client = None,
            kms_crypto_client = None,
            generate_key_details = None,
            vault_client = None,
            secrets_client = None)

        # Perform test
        _oci_clients = aOCIClients
        self.assertIsInstance(_oci_clients, OCIClients)
        self.assertIsNone(_oci_clients.kms_crypto_client)
        self.assertIsNone(_oci_clients.generate_key_details)

    #
    # Test createVaultClients
    #

    #
    # Test deleteEncryptionMarkerFileForVM
    #
    def test_deleteEncryptionMarkerFileForVM_whole_dir(self):
        """
        Test deleteEncryptionMarkerFileForVM
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*rm", aRc=0),
                    exaMockCommand("/bin/rm -rf /opt/exacloud/fs_encryption", aRc=0)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        for _dom0, _ in ebox.mReturnDom0DomUPair():
            self.assertEqual(None, deleteEncryptionMarkerFileForVM(_dom0))

    def test_deleteEncryptionMarkerFileForVM_vm_name(self):
        """
        Test deleteEncryptionMarkerFileForVM
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*rm", aRc=0),
                    exaMockCommand("/bin/rm -rf /opt/exacloud/fs_encryption", aRc=0)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        for _dom0, _domU in ebox.mReturnDom0DomUPair():
            self.assertEqual(None, deleteEncryptionMarkerFileForVM(_dom0, _domU))
    #
    # Test deleteEncryptionMarkerFileForVM
    #

    #
    # Test createEncryptionMarkerFileForVM
    #
    def test_createEncryptionMarkerFileForVM_specific_vm(self):
        """
        Test createEncryptionMarkerFileForVM
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*mkdir", aRc=0),
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/fs_encryption", aRc=0),
                    exaMockCommand("test.*touch", aRc=0),
                    exaMockCommand("touch /opt/exacloud/fs_encryption/fs_encryption_keyapi_[^\.].+", aRc=0)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        for _dom0, _domU in ebox.mReturnDom0DomUPair():
            self.assertEqual(None, createEncryptionMarkerFileForVM(_dom0, _domU))

    #
    # Test createEncryptionMarkerFileForVM
    #


    #
    # Test createAndPushRemotePassphraseSetup SIV
    #

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.ovm.cluencryption.checkRemotePassphraseNotPresentSiV")
    @patch("exabox.ovm.cluencryption.SecretsClient")
    @patch("exabox.ovm.cluencryption.createOCIClientsSetup")
    @patch("exabox.ovm.cluencryption.OCIClients")
    @patch('oci.vault.VaultsClientCompositeOperations.create_secret_and_wait_for_state')
    def test_createAndPushRemotePassphraseSetup_siv_no_present_key_all_good(self,
            aMagicCompositeOps, aOCIClients, createOCIClientsSetup, 
            aMagicSecretClient, deleteRemotePassphraseSiV, 
            aMagicR1):
        """
        This method is used to test the creation of a passphrase for a given
        list of domU with SiV
        """
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload

        # Attempt deletion as if we were in non R1
        aMagicR1.return_value = False

        # Mock composite operations
        aMagicCompositeOps.return_value = MagicMock()

        # Modify Secret Client get_secret_bundle_by_name
        # call to pretend secret is not present
        aMagicSecretClient.return_value.get_secret_bundle_by_name = Exception(
                "No secret passphrase is present")

        deleteRemotePassphraseSiV.side_effect = None

        # Get list of domus
        _ebox = self.mGetClubox()
        _domu_list = [ _domu for _ , _domu in _ebox.mReturnDom0DomUPair()]
        self.assertEqual(None, createAndPushRemotePassphraseSetup(_json, _domu_list))

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.exaoci.ExaOCIFactory.VaultsClient")
    @patch("exabox.exaoci.ExaOCIFactory.SecretsClient")
    @patch("exabox.ovm.cluencryption.ExaOCIFactory")
    @patch('oci.vault.VaultsClientCompositeOperations.create_secret_and_wait_for_state')
    def test_createAndPushRemotePassphraseSetup_siv_key_present_create_new_passphrase(self,
            aMagicCompositeOps, aExaOCIFactory, aMagicSecretClient,
            aMagicVaultClient, aMagicR1):
        """
        This method is used to test the creation of a passphrase for a given
        list of domU with SiV
        """
        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload

        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Attempt deletion as if we were in non R1
        aMagicR1.return_value = False

        # Mock composite operations
        aMagicCompositeOps.return_value = MagicMock()


        aExaOCIFactory.return_value.get_secrets_client.return_value = aMagicSecretClient
        aExaOCIFactory.return_value.get_vault_client.return_value = aMagicVaultClient

        # Get list of domus
        _ebox = self.mGetClubox()
        _domu_list = [ _domu for _ , _domu in _ebox.mReturnDom0DomUPair()]
        self.assertEqual(None, createAndPushRemotePassphraseSetup(_json, _domu_list))

    #
    # Test createAndPushRemotePassphraseSetup SIV
    #

    #
    # Test deleteRemotePassphraseSetup SIV
    #
    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.ovm.cluencryption.checkRemotePassphraseNotPresentSiV")
    @patch("exabox.ovm.cluencryption.SecretsClient")
    @patch("exabox.ovm.cluencryption.createOCIClientsSetup")
    @patch("exabox.ovm.cluencryption.OCIClients")
    def test_deleteRemotePassphraseSetup_siv_delete_ok(self,
            aOCIClients, createOCIClientsSetup, 
            aMagicSecretClient, deleteRemotePassphraseSiV, 
            aMagicR1):
        """
        Function to test deletion of remote passphrase from SIV
        """

        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Attempt deletion as if we were in non R1
        aMagicR1.return_value = False

        # Get list of domus
        _ebox = self.mGetClubox()
        _domu_list = [ _domu for _ , _domu in _ebox.mReturnDom0DomUPair()]
        self.assertEqual(None, deleteRemotePassphraseSetup(_json, _domu_list))

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.exaoci.ExaOCIFactory.VaultsClient")
    @patch("exabox.exaoci.ExaOCIFactory.ObjectStorageClient")
    @patch("exabox.ovm.cluencryption.ExaOCIFactory")
    def test_deleteRemotePassphraseSetup_siv_delete_fails(self,
            aExaOCIFactory, aMagicObjectStorageClient, 
            aMagicVaultClient, aMagicR1):
        """
        Function to test deletion of remote passphrase from SIV
        """

        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Attempt deletion as if we were in non R1
        aMagicR1.return_value = False

        # Modify Object Storage Client get_object call to pretend no key
        # is present
        aMagicObjectStorageClient.delete_object.side_effect = Exception("Unable "
                "to delete")
        aExaOCIFactory.return_value.get_object_storage_client.return_value = aMagicObjectStorageClient

        # # Modify Vault Client to fake failure of deletion scheduling
        aMagicVaultClient.schedule_secret_deletion.side_effect = Exception("Unable "
                "to schedule deletion")
        aExaOCIFactory.return_value.get_vault_client.return_value = aMagicVaultClient

        # Get list of domus
        _ebox = self.mGetClubox()
        _domu_list = [ _domu for _ , _domu in _ebox.mReturnDom0DomUPair()]
        self.assertRaises(ExacloudRuntimeError, lambda: deleteRemotePassphraseSetup(_json, _domu_list))

    @patch("exabox.ovm.cluencryption.mIsR1")
    @patch("exabox.ovm.cluencryption.checkRemotePassphraseNotPresentSiV")
    @patch("exabox.ovm.cluencryption.SecretsClient")
    @patch("exabox.ovm.cluencryption.createOCIClientsSetup")
    @patch("exabox.ovm.cluencryption.OCIClients")
    def test_deleteRemotePassphraseSetup_siv_no_passphrase_present(self,
            aOCIClients, createOCIClientsSetup, 
            aMagicSecretClient, deleteRemotePassphraseSiV, 
            aMagicR1):
        """
        Function to test deletion of remote passphrase from SIV
        """

        _json = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _json.jsonconf["fs_encryption"] = _enc_payload


        # Get information from payload about the OCI resources to be used to store/encrypt
        # the passphrase
        _remote_oci_resources = parseEncryptionPayload(_json, "domU")

        # Attempt deletion as if we were in non R1
        aMagicR1.return_value = False

        # Modify Vault Client to fake no passphrase exists
        aMagicSecretClient.return_value.get_secret_bundle_by_name = Exception("Unable "
                "to find remote passphrase")

        # Get list of domus
        _ebox = self.mGetClubox()
        _domu_list = [ _domu for _ , _domu in _ebox.mReturnDom0DomUPair()]
        self.assertEqual(None, deleteRemotePassphraseSetup(_json, _domu_list))

    #
    # Test deleteRemotePassphraseSetup SIV
    #


    #
    # Test createLocalFSKey
    #
    def test_mCreateLocalFSKey(self):
        """
        This funciton tests the creation of the dummy key file
        used for dev testing envionments
        """

        _key_file = "/etc/fs_crypt_key"
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(f"test -e {_key_file}", aRc=1),
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand("dd if=/dev/random", aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        for _dom0, _domU in ebox.mReturnDom0DomUPair():
            with connect_to_host(_domU, get_gcontext()) as _node:
                self.assertRaises(Exception,
                    lambda: createLocalFSKey(_node))
    #
    # Test createLocalFSKey
    #

    #
    # ensureSystemFirstBootEncryptedExists
    #
    def test_ensureSystemFirstBootEncryptedExists_all_good_already_present_both(self):
        """
        Function to test ensureSystemFirstBootEncryptedExists
        """
        # Declare commands
        _version = "21.2.10.0.0.220317"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test -e ", aRc=0),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0, aStdout=f"{_version}", aPersist=True),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=0, aStdout=f"{_version}", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0, aStdout=f"{_version}", aPersist=True),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=0, aStdout=f"{_version}", aPersist=True),
                ],
                [
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0, aStdout=f"{_version}", aPersist=True),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=0, aStdout=f"{_version}", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _results = []
        _ebox = self.mGetClubox()

        # Run test
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value=_version),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value='X9'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value='X9'):
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _results.append(ensureSystemFirstBootEncryptedExists(_ebox, _dom0))

        self.assertEqual([None, None], _results)

    def test_ensureSystemFirstBootEncryptedExists_all_good_create_encrypted(self):
        """
        Function to test ensureSystemFirstBootEncryptedExists
        """

        # Declare commands
        _version = "21.2.10.0.0.220317"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test -e ", aRc=0),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=1),
                    exaMockCommand(f"/opt/exadata_ovm/vm_maker --encrypt /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                ],
                [
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=1),
                    exaMockCommand(f"/opt/exadata_ovm/vm_maker --encrypt /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=1),
                    exaMockCommand(f"/opt/exadata_ovm/vm_maker --encrypt /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _results = []
        _ebox = self.mGetClubox()

        # Run test
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value=_version),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value='X9'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value='X9'):
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                _results.append(ensureSystemFirstBootEncryptedExists(_ebox, _dom0))

        self.assertEqual([None, None], _results)

    def test_ensureSystemFirstBootEncryptedExists_fail_to_create_encrypted(self):
        """
        Function to test ensureSystemFirstBootEncryptedExists
        """

        # Declare commands
        _version = "21.2.10.0.0.220317"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test -e ", aRc=0),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                ],
                [
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=1),
                    exaMockCommand(f"/opt/exadata_ovm/vm_maker --encrypt /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=1),
                ],
                [
                    exaMockCommand(f"/bin/test -e .",
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _results = []
        _ebox = self.mGetClubox()

        # Run test
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            self.assertRaises(ExacloudRuntimeError,
                lambda: ensureSystemFirstBootEncryptedExists(_ebox, _dom0))

    def test_ensureSystemFirstBootEncryptedExists_fail_to_calculate_non_encrypted_img(self):
        """
        Function to test ensureSystemFirstBootEncryptedExists
        """

        # Declare commands
        _version = "21.2.10.0.0.220317"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test -e ", aRc=0),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                ],
                [
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=1),
                ],
                [
                    exaMockCommand(f"/bin/test -e .")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _results = []
        _ebox = self.mGetClubox()

        # Run test
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            self.assertRaises(ExacloudRuntimeError,
                lambda: ensureSystemFirstBootEncryptedExists(_ebox, _dom0))

    def test_ensureSystemFirstBootEncryptedExistsParallelSetup_all_good(self):
        """
        This function is to test ensureSystemFirstBootEncryptedExistsParallelSetup
        """

        # Declare commands
        _version = "21.2.10.0.0.220317"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test -e ", aRc=0),
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aRc=0, aStdout=f"{_version}"),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=1),
                    exaMockCommand(f"/opt/exadata_ovm/vm_maker --encrypt /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                ],
                [
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /EXAVMIMAGES/System.first.boot.{_version}.encrypted.img",
                        aRc=1),
                    exaMockCommand(f"/opt/exadata_ovm/vm_maker --encrypt /EXAVMIMAGES/System.first.boot.{_version}.img",
                        aRc=0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variables
        _results = []
        _ebox = self.mGetClubox()

        # Run test
        #def ensureSystemFirstBootEncryptedExistsParallelSetup(aCluCtrl: any, aDom0List: str):
        _dom0_list = [ _dom0  for _dom0 , _ in _ebox.mReturnDom0DomUPair()]
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value=_version),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model', return_value='X9'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value='X9'):
            self.assertEqual(None, (ensureSystemFirstBootEncryptedExistsParallelSetup(_ebox, _dom0_list)))

    #
    # ensureSystemFirstBootEncryptedExists
    #

    #
    # copyOEDAKeyApiToNode
    #

    def test_copyOEDAKeyApiToNode_all_good_r1_not_present(self):
        """
        Function to test copyOEDAKeyApiToNode
        """

        # Declare variables
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()

        _clu_name = _ebox.mGetClusters().mGetCluster().mGetCluName()
        _remote_keyapi_dir = os.path.join("/tmp", "fs_encryption")
        _keyapi_name = f"fs_encryption_keyapi_{_clu_name}"
        _remote_keyapi_path = os.path.join(_remote_keyapi_dir, _keyapi_name)

        # Declare commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test -e {_remote_keyapi_path}", aRc=1),
                    exaMockCommand(f"test -e ", aRc=0, aPersist=True),
                    exaMockCommand(f"mkdir -p {_remote_keyapi_dir}", aRc=0),
                    exaMockCommand(f"scp scripts/fs_encryption/fs_encryption_key_api_oeda_r1.sh {_remote_keyapi_path}", aRc=0),
                    exaMockCommand(f"chown root:root {_remote_keyapi_path}", aRc=0),
                    exaMockCommand(f"chmod 500 {_remote_keyapi_path}", aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Set options to use local passphrase
        self.mGetContext().mSetConfigOption('env_type', 'DEV')
        self.mGetContext().mSetConfigOption('local_fs_passphrase', 'True')

        # Run Test
        _results = []
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            _results.append(copyOEDAKeyApiToNode(_dom0, _remote_keyapi_path, 
                _domU, _options, False))

        self.assertEqual([None, None], _results)

        self.mGetContext().mSetConfigOption('local_fs_passphrase', 'False')

    #
    # copyOEDAKeyApiToNode
    #

    #
    # Test useLocalPassphrase
    #
    def test_useLocalPassphrase_dev_env_local_pass(self):
        """
        Function to test useLocalPassphrase
        """

        # Set options
        self.mGetContext().mSetConfigOption('env_type', 'DEV')
        self.mGetContext().mSetConfigOption('local_fs_passphrase', 'True')

        # Run test
        self.assertEqual(True, useLocalPassphrase())

    def test_useLocalPassphrase_prod_env_local_pass(self):
        """
        Function to test useLocalPassphrase
        """

        # Set options
        self.mGetContext().mSetConfigOption('env_type', 'prod')
        self.mGetContext().mSetConfigOption('local_fs_passphrase', 'True')

        # Run test
        self.assertEqual(False, useLocalPassphrase())

    def test_useLocalPassphrase_prod_env_remote_pass(self):
        """
        Function to test useLocalPassphrase
        """

        # Set options
        self.mGetContext().mSetConfigOption('env_type', 'prod')
        self.mGetContext().mSetConfigOption('local_fs_passphrase', None)

        # Run test
        self.assertEqual(False, useLocalPassphrase())
    #
    # Test useLocalPassphrase
    #

    #
    # Test deleteOEDAKeyApiFromDom0
    #
    def test_deleteOEDAKeyApiFromDom0(self):
        """
        Function to test deleteOEDAKeyApiFromDom0
        """

        _key_file = "/opt/exacloud/fs_encryption/fs_encryption_keyapi_clu*"
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand(f"rm -f {_key_file}")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _dom0_list = [ _dom0 for _dom0 , _ in ebox.mReturnDom0DomUPair()]
        deleteOEDAKeyApiFromDom0(ebox, _dom0_list)


    #
    # Test deleteOEDAKeyApiFromDom0
    #

    #
    # Test RSAEncryption
    #
    def test_RSAEncryption(self):
        """
        This funciton tests the RSA Encryption by loading a private & public key 
        & encrypts a symmetric key using the public key & decrpt a symmetric key using the private Key.
        Symmetric Encryption can be tested by generating a symmetric key & encrypts the user data.
        """
        _rsa_obj = RSAEncryption()
        _rsa_obj.mLoadPublicKey(PUB_KEY)

        _symmetric_obj = SymmetricEncryption()
        _symmetric_key = _symmetric_obj.mGetKey()

        _encrypted_symmetric_key = _rsa_obj.mEncryptKey(_symmetric_key)

        _rsa_obj.mLoadPrivateKey(PRIV_KEY)
        _decrypted_symmetric_key = _rsa_obj.mDecryptKey(_encrypted_symmetric_key)
        self.assertEqual(_symmetric_key, _decrypted_symmetric_key)

        _user_data = USER_DATA.encode()
        _encrypted_data = _symmetric_obj.mEncrypt(_user_data)
        _data = _symmetric_obj.mDecrypt(_encrypted_data)
        self.assertEqual(_user_data, _data)

    #
    # Test setupU01EncryptedDiskPerHost
    #
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDyndepFilesList')
    @patch('exabox.ovm.cluencryption.attachEncryptedVDiskToKVMGuest')
    @patch('exabox.ovm.cluencryption.createEncryptedLVM')
    @patch('exabox.ovm.cluencryption.copyOEDAKeyApiToNode')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories')
    @patch("exabox.ovm.cluencryption.getMountPointInfo")
    def test_setupU01EncryptedDiskPerHost(self, aMockMountInfo, aMockOraBaseDirs, aMockCopyImage, aMockCreateImage, aMockAttachImage, aMockDynDep):
        """
        This function tests setupU01EncryptedDiskPerHost
        """

        aMockDynDep.return_value = ("19.08", None)
        # Mock exabox commands
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -e .*", aRc=0, aPersist=True),
                    exaMockCommand("findmnt -rno source,fstype,label .*",
                        aRc=0,
                        aStdout="/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk xfs \n"),
                    exaMockCommand("systemd-analyze time", aRc=0),

                    # stop service
                    exaMockCommand("crsctl stop crs -f",
                        aRc=0,
                        aStdout=(
                            "CRS-4133: Oracle High Availability Services has been stopped.\n")),

                    # Check processes using /u01
                    exaMockCommand("lsof -- /u01",
                        aRc=0,
                        aStdout=(
                            "COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF     "
                            "NODE NAME\n"
                            "java    86383 root   59r   REG  252,1 10628677 "
                            "17053718 /u01/app/grid/diag/crs/atpd-exa-dfuwg2/crs/trace/diskmon.trc\n")),

                    # kill any process still alive
                    exaMockCommand("/bin/kill -9 .*",
                        aRc=0,
                        aStdout=""),

                    # Check again processes using /u01
                    exaMockCommand("lsof -- /u01",
                        aRc=0,
                        aStdout=(
                            "COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF     "
                            "NODE NAME\n")),

                    # umount /u01
                    exaMockCommand("umount -R /u01",
                        aRc=0,),

                    # Log fstab
                    exaMockCommand("cat /etc/fstab",
                        aRc=0,
                        aStdout=(
                            "LABEL=BOOT              /boot   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=DBSYS             /       xfs     defaults        0 0\n"
                            "LABEL=SWAP              swap    swap    defaults        0 0\n"
                            "LABEL=HOME              /home   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=VAR               /var    xfs     defaults,nodev  0 0\n"
                            "LABEL=DIAG              /var/log        xfs     defaults,nodev,nosuid   0 0\n"
                            "tmpfs           /dev/shm        tmpfs   defaults,nodev,size=88080m 0 0\n"
                            "LABEL=KDUMP             /crashfiles     xfs     defaults,nodev  0 0\n"
                            "LABEL=TMP               /tmp    xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=AUDIT             /var/log/audit  xfs     defaults,nodev,noexec,nosuid    0 0\n"
                            "/dev/VGExaDbDisk.grid19.0.0.0.230718.img/LVDBDisk               /u01/app/19.0.0.0/grid  xfs     defaults,nodev  0 0\n"
                            "/dev/VGExaDbDisk.u01.20.img/LVDBDisk            /u01    xfs     defaults,nodev  0 0\n"
                            "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt          /u02    ext4    defaults 0 0\n"
                            "HUGEPAGES      /dev/hugepages      hugetlbfs       defaults,mode=0777      0 0\n"
                            )),

                    # Delete u01 entry
                    exaMockCommand("sed -i .*/etc/fstab", aRc=0),

                    exaMockCommand("cat /etc/fstab",
                        aRc=0,
                        aStdout=(
                            "LABEL=BOOT              /boot   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=DBSYS             /       xfs     defaults        0 0\n"
                            "LABEL=SWAP              swap    swap    defaults        0 0\n"
                            "LABEL=HOME              /home   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=VAR               /var    xfs     defaults,nodev  0 0\n"
                            "LABEL=DIAG              /var/log        xfs     defaults,nodev,nosuid   0 0\n"
                            "tmpfs           /dev/shm        tmpfs   defaults,nodev,size=88080m 0 0\n"
                            "LABEL=KDUMP             /crashfiles     xfs     defaults,nodev  0 0\n"
                            "LABEL=TMP               /tmp    xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=AUDIT             /var/log/audit  xfs     defaults,nodev,noexec,nosuid    0 0\n"
                            "/dev/VGExaDbDisk.grid19.0.0.0.230718.img/LVDBDisk               /u01/app/19.0.0.0/grid  xfs     defaults,nodev  0 0\n"
                            "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt          /u02    ext4    defaults 0 0\n"
                            "HUGEPAGES      /dev/hugepages      hugetlbfs       defaults,mode=0777      0 0\n"
                            )),
                ],
                [
                    exaMockCommand("systemd-analyze time", aRc=0),
                    exaMockCommand("crsctl check crs",
                        aRc=0,
                        aStdout=(
                            "CRS-4638: Oracle High Availability Services is online\n"
                            "CRS-4537: Cluster Ready Services is online\n"
                            "CRS-4529: Cluster Synchronization Services is online\n"
                            "CRS-4533: Event Manager is online\n")),
                ],
                [
                    exaMockCommand("grep grid /etc/fstab", aRc=0,
                        aStdout=(
                            "/dev/VGExaDbDisk.grid19.0.0.0.230718.img/LVDBDisk               /u01/app/19.0.0.0/grid  xfs     defaults,nodev  0 0\n")),
                    exaMockCommand("/bin/mkdir -p /u01/app/19.0.0.0/grid", aRc=0),
                    exaMockCommand("test -e.*grep", aRc=0),
                    exaMockCommand("test -e.*cat", aRc=0),
                    exaMockCommand("test -e.*cat", aRc=0),
                    exaMockCommand("cat /etc/fstab", aRc=0,
                        aStdout=(
                            "LABEL=BOOT              /boot   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=DBSYS             /       xfs     defaults        0 0\n"
                            "LABEL=SWAP              swap    swap    defaults        0 0\n"
                            "LABEL=HOME              /home   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=VAR               /var    xfs     defaults,nodev  0 0\n"
                            "LABEL=DIAG              /var/log        xfs     defaults,nodev,nosuid   0 0\n"
                            "tmpfs           /dev/shm        tmpfs   defaults,nodev,size=29616m 0 0\n"
                            "LABEL=KDUMP             /crashfiles     xfs     defaults,nodev  0 0\n"
                            "LABEL=TMP               /tmp    xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=AUDIT             /var/log/audit  xfs     defaults,nodev,noexec,nosuid    0 0\n"
                            "/dev/VGExaDbDisk.grid19.0.0.0.230718.img/LVDBDisk               /u01/app/19.0.0.0/grid  xfs     defaults,nodev  0 0\n"
                            "/dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk-crypt                /u01    xfs     defaults 0 0\n"
                            "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt          /u02    ext4    defaults 0 0\n"

                            )),
                    exaMockCommand("sed.*", aRc=0),
                    exaMockCommand("cat /etc/fstab", aRc=0,
                        aStdout=(
                            "LABEL=BOOT              /boot   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=DBSYS             /       xfs     defaults        0 0\n"
                            "LABEL=SWAP              swap    swap    defaults        0 0\n"
                            "LABEL=HOME              /home   xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=VAR               /var    xfs     defaults,nodev  0 0\n"
                            "LABEL=DIAG              /var/log        xfs     defaults,nodev,nosuid   0 0\n"
                            "tmpfs           /dev/shm        tmpfs   defaults,nodev,size=29616m 0 0\n"
                            "LABEL=KDUMP             /crashfiles     xfs     defaults,nodev  0 0\n"
                            "LABEL=TMP               /tmp    xfs     defaults,nodev,nosuid   0 0\n"
                            "LABEL=AUDIT             /var/log/audit  xfs     defaults,nodev,noexec,nosuid    0 0\n"
                            "/dev/VGExaDbDisk.grid19.0.0.0.230718.img/LVDBDisk               /u01/app/19.0.0.0/grid  xfs     defaults,nodev  0 0\n"
                            "/dev/mapper/VGExaDbDisk.u01_encrypted.img-LVDBDisk-crypt                /u01    xfs     defaults 0 0\n"
                            "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt          /u02    ext4    defaults 0 0\n"

                            )),
                ],
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e.*vm_maker"),
                    exaMockCommand("test -e.*rm"),
                    exaMockCommand("test -e.*zip"),
                    exaMockCommand("test -e.*touch"),
                    exaMockCommand("test -e.*mkdir"),
                    exaMockCommand("test -e.*mkdir"),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/GlobalCache/.*"),
                    exaMockCommand("touch /EXAVMIMAGES/GlobalCache/.*u01_encrypted.marker"),
                    exaMockCommand("zip /EXAVMIMAGES/GlobalCache/.*u01_encrypted.zip .*u01_encrypted.marker"),
                    exaMockCommand("vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com",
                        aRc=0, aStdout=(
                            "File /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/System.img\n"
                            "File /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/grid19.0.0.0.230718.img\n"
                            "File /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01.img\n"
                            "File /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02_extra_encrypted.img\n")),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/System.img"),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/grid19.0.0.0.230718.img"),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01.img"),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02_extra_encrypted.img"),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01_encrypted.img"),
                    exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01_encrypted.img"),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01.img"),
                    exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01.img"),
                    exaMockCommand("vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u01.img --domain scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02_extra_encrypted.img --domain scaqab10client01vm08.us.oracle.com"),
                ]
            ]

        }

        self.mPrepareMockCommands(_cmds)

        # Mock objects
        aMockMountInfo.return_value = MountPointInfo(
                is_luks = False,
                block_device= "/dev/mapper/VGExaDbDisk.u01.20.img-LVDBDisk",
                fs_type= "xfs",
                fs_label= "",
                luks_device= "",
                mount_point= "/u01"
                )
        aMockOraBaseDirs.return_value = ("/u01/app/19.0.0.0/grid/", "1900", None)

        # Declare variables to use
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        _enc_payload = self.mGetUtil().mReadJson(
                self.PATH_ENCRYPTION_PAYLOAD_SIV)

        _options.jsonconf["fs_encryption"] = _enc_payload
        _options.jsonconf["filesystems"] = {
                "mountpoints": {
                    "/": "15G",
                    "/home": "4G",
                    "/tmp": "10G",
                    "/u01": "250G",
                    "/var": "10G",
                    "/var/log": "30G",
                    "/var/log/audit": "3G",
                    "grid": "50G"
                }
        }

        # Run test
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        self.assertEqual(0, setupU01EncryptedDiskPerHost(
            _ebox, _options, _dom0, _domU, aMountPoint="/u01"))

    #
    # Test createEncryptedLVMVmMaker
    #
    def test_createEncryptedLVMVmMaker_msdosno_gdisk(self):
        """
        Tests createEncryptedLVMVmMaker
        """

        # Mock exabox commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img", aRc=1),
                    exaMockCommand("test.*vm_maker", 0),
                    exaMockCommand("test.*grep", 0),
                    exaMockCommand("vm_maker -h | /bin/grep -- '--create --disk-image ' | /bin/grep 'label' -i ", 0,
                        aStdout="msdos"),
                    exaMockCommand("vm_maker --create --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img --size 60 --filesystem ext4 --from-zip /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.zip --label msdos --encrypt", 0),
                ],
                [
                ]
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _zip_remote_file_path = f"/EXAVMIMAGES/GuestImages/{_domU}/u02.zip"
        createEncryptedLVMVmMaker(_dom0, _domU, _ebox, _zip_remote_file_path,
            "60", "ext4")

    def test_createEncryptedLVMVmMaker_gpt_no_exabox_conf(self):
        """
        Tests createEncryptedLVMVmMaker
        """

        # Mock exabox commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img", aRc=1),
                    exaMockCommand("test.*vm_maker", 0),
                    exaMockCommand("test.*grep", 0),
                    exaMockCommand("vm_maker -h | /bin/grep -- '--create --disk-image ' | /bin/grep 'label' -i ", 1),
                    exaMockCommand("vm_maker --create --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img --size 60 --filesystem ext4 --from-zip /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.zip --label msdos --encrypt", 0),
                [
                ],
                ]
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _zip_remote_file_path = f"/EXAVMIMAGES/GuestImages/{_domU}/u02.zip"
        self.mGetContext().mSetConfigOption(
                'fs_encryption_allow_msdos_gdisk_conversion', 'false')
        self.assertRaises(ExacloudRuntimeError,
            lambda: createEncryptedLVMVmMaker(_dom0, _domU, _ebox, _zip_remote_file_path,
            "60", "ext4"))


    def test_createEncryptedLVMVmMaker_gpt_with_gdisk_missing(self):
        """
        Tests createEncryptedLVMVmMaker
        """

        # Mock exabox commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img", aRc=1),
                    exaMockCommand("test.*vm_maker", 0),
                    exaMockCommand("test.*grep", 0),
                    exaMockCommand("vm_maker -h | /bin/grep -- '--create --disk-image ' | /bin/grep 'msdos' -i ", 1),
                    exaMockCommand("vm_maker --create --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img --size 60 --filesystem ext4 --from-zip /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.zip --label msdos --encrypt", 0),
                ],
                [
                ]
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _zip_remote_file_path = f"/EXAVMIMAGES/GuestImages/{_domU}/u02.zip"
        self.mGetContext().mSetConfigOption(
                'fs_encryption_allow_msdos_gdisk_conversion', 'true')
        self.assertRaises(ExacloudRuntimeError,
            lambda: createEncryptedLVMVmMaker(_dom0, _domU, _ebox, _zip_remote_file_path,
            "60", "ext4"))


    @patch("exabox.ovm.cluencryption.convertGptToMsdosLabelDriver")
    @patch("exabox.ovm.cluencryption.glob.glob")
    def test_createEncryptedLVMVmMaker_gpt_with_gdisk_present(
            self, aMagicGlob, aMagicConvertLabel):
        """
        Tests createEncryptedLVMVmMaker
        """

        # Mock exabox commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img", aRc=1),
                    exaMockCommand("test.*vm_maker", 0),
                    exaMockCommand("test.*grep", 0),
                    exaMockCommand("vm_maker -h | /bin/grep -- '--create --disk-image ' | /bin/grep 'msdos' -i ", 1),
                    exaMockCommand("vm_maker --create --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.img --size 60 --filesystem ext4 --from-zip /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02.zip  --encrypt", 0),
                ],
                [
                ],
                [
                ]
            ]

        }

        self.mPrepareMockCommands(_cmds)
        aMagicGlob.return_value = ["images/gdisk.x86_64.rpm"]

        _ebox = self.mGetClubox()
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _zip_remote_file_path = f"/EXAVMIMAGES/GuestImages/{_domU}/u02.zip"
        self.mGetContext().mSetConfigOption(
                'fs_encryption_allow_msdos_gdisk_conversion', 'true')
        self.assertEqual(None,
            createEncryptedLVMVmMaker(_dom0, _domU, _ebox, _zip_remote_file_path,
            "60", "ext4"))

    #
    # Test validateMinImgEncryptionSupport
    #
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataImageFromMap')
    def test_validateMinImgEncryptionSupport(self, aMagicExaImage):
        """
        Validate validateMinImgEncryptionSupport
        """

        _ebox = self.mGetClubox()
        self.mGetContext().mSetConfigOption('fs_encryption_cutoff_ver_24.1_dom0', '24.1.1.0.0.240208')
        self.mGetContext().mSetConfigOption('fs_encryption_cutoff_ver_24.1_domU', '24.1.1.0.0.240208')
        self.mGetContext().mSetConfigOption('fs_encryption_cutoff_ver_23.1_dom0', '23.1.1.0.0.240308')
        self.mGetContext().mSetConfigOption('fs_encryption_cutoff_ver_23.1_domU', '23.1.1.0.0.240308')

        # Same value 4 times, 1 for each node
        aMagicExaImage.side_effect = ["24.1.1.0.0.240210", "24.1.1.0.0.240210", "24.1.1.0.0.240210", "24.1.1.0.0.240210"]
        self.assertEqual(True, validateMinImgEncryptionSupport(
            _ebox,  _ebox.mReturnDom0DomUPair()))


        # Same value 4 times, 1 for each node
        aMagicExaImage.side_effect = ["24.1.1.0.0.240110", "24.1.1.0.0.240210", "24.1.1.0.0.240210", "24.1.1.0.0.240210"]
        self.assertEqual(False, validateMinImgEncryptionSupport(
            _ebox,  _ebox.mReturnDom0DomUPair()))

    #
    # Test convertGptToMsdosLabelDriver
    #
    def test_convertGptToMsdosLabelDriver(self):
        """
        Tests convertGptToMsdosLabelDriver
        """

        # Mock exabox commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e.*partprobe"),
                    exaMockCommand("partprobe /EXAVMIMAGES/GuestImages/u01provluks2-vcejx1.client.exaclouddev.oraclevcn.com/u02_extra_encrypted.img -ds",
                        aStdout="/EXAVMIMAGES//GuestImages/u01provluks2-vcejx1.client.exaclouddev.oraclevcn.com/u02_     extra_encrypted.img: gpt partitions 1\n"),
                    exaMockCommand("test -e.*rpm"),
                    exaMockCommand("rpm -q gdisk", aStdout="package gdisk is not installed\n",
                        aRc=1),
                    exaMockCommand("scp images/gdisk.x86_64.rpm /tmp/gdisk.x86_64.rpm",
                        aRc=0),
                    exaMockCommand("rpm -ivh /tmp/gdisk.x86_64.rpm",
                        aStdout=(
                            "Verifying...                          ################################# [100%]\n"
                            "Preparing...                          ################################# [100%]\n"
                            "Updating / installing...\n"
                            "   1:gdisk-1.0.3-11.el8               ################################# [100%]\n"
                            ),
                        aRc=0),
                    exaMockCommand("test -e.*rpm"),
                    exaMockCommand("rpm -q gdisk", aStdout="gdisk-1.0.3-11.el8.x86_64",
                        aRc=0),
                    exaMockCommand("rpm -e --allmatches gdisk",
                        aStdout=(
                            "Verifying...                          ################################# [100%]\n"
                            "Preparing...                          ################################# [100%]\n"
                            "Updating / installing...\n"
                            "   1:gdisk-1.0.3-11.el8               ################################# [100%]\n"
                            ),
                        aRc=0),
                    exaMockCommand("test -e.*gdisk"),
                    exaMockCommand("/bin/echo -e .*"),
                ]
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0, _ = _ebox.mReturnDom0DomUPair()[0]
        convertGptToMsdosLabelDriver(_dom0,
                "/EXAVMIMAGES/GuestImages/u01provluks2-vcejx1.client.exaclouddev.oraclevcn.com/u02_extra_encrypted.img")

    def test_cleanupU02EncryptedDisk(self):
        """
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/GuestImages/scaqab10client0[12]vm08.us.oracle.com/u02_extra_encrypted.img", aRc=0),
                    exaMockCommand("vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client0[12]vm08.us.oracle.com/u02_extra_encrypted.img --domain scaqab10client0[12]vm08.us.oracle.com", aRc=0),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/scaqab10client0[12]vm08.us.oracle.com/u02_extra_encrypted.img", aRc=0),
                    exaMockCommand("/bin/test -e /bin/virsh", aRc=0, aPersist=True),
                    exaMockCommand("virsh shutdown", aRc=0),
                    exaMockCommand("virsh list --name --state-running --state-paused", aRc=0),
                    exaMockCommand("virsh list --name", aRc=0),
                    exaMockCommand("virsh list --name", aRc=0),
                    exaMockCommand("virsh start", aRc=0),
                    exaMockCommand("virsh list --name --state-running --state-paused", aRc=0,
                        aStdout="scaqab10client0[12]vm08.us.oracle.com\n"),
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("unmount /u02"),
                    exaMockCommand("test.*cryptsetup"),
                    exaMockCommand("cryptsetup close /dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt"),
                    exaMockCommand("cat /etc/fstab | grep -v /u02 > /etc/fstab.orig; cp /etc/fstab.orig /etc/fstab"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0, _ = _ebox.mReturnDom0DomUPair()[0]
        cleanupU02EncryptedDisk(_ebox.mReturnDom0DomUPair())

    def test_mSetLuksPassphraseOnDom0Exacc(self):
        """
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /sbin/shred",
                        aRc=0,),
                    exaMockCommand("/usr/bin/virsh domid scaqab10client01vm08.us.oracle.com",
                        aRc=0, aStdout="12\n"),
                    exaMockCommand("/bin/ls /var/lib/libvirt/qemu/channel/target/domain-12\*/vmfsexacc",
                        aRc=0, aStdout="/var/lib/libvirt/qemu/channel/target/domain-12-someqemuid/vmfsexacc"),
                ],
                [
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/bin",
                        aRc=0),
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/fs_encryption/passphrases",
                        aRc=0),
                    exaMockCommand("/bin/touch /opt/exacloud/fs_encryption/passphrases/fs_enc_scaqab10client01vm08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("/bin/scp scripts/fs_encryption/create_socket.py /opt/exacloud/bin/create_socket.py",
                        aRc=0),
                    exaMockCommand("/bin/test -e /sbin/nohup",
                        aRc=0),
                    exaMockCommand('/sbin/nohup /bin/sh -c "/usr/bin/python3 /opt/exacloud/bin/create_socket.py -vm scaqab10client01vm08.us.oracle.com -file /opt/exacloud/fs_encryption/passphrases/fs_enc_scaqab10client01vm08.us.oracle.com -wait 300 " & # pass NOLOG',
                        aRc=0),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/exacloud/fs_encryption/passphrases/fs_enc_scaqab10client01vm08.us.oracle.com",
                        aRc=0),
                    exaMockCommand("/bin/test -e /sbin/shred",
                        aRc=0,),
                    exaMockCommand("shred -u /opt/exacloud/fs_encryption/passphrases/fs_enc_scaqab10client01vm08.us.oracle.com",
                        aRc=1,),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _ebox.mSetOciExacc(True)
        _ebox.mSetEnableKVM(True)
        self.assertEqual("",
            mSetLuksPassphraseOnDom0Exacc(_ebox, _dom0, _domU, aWait=False, aWaitSeconds=300))

if __name__ == '__main__':
    unittest.main()

