#
# $Header: ecs/exacloud/exabox/ovm/cluencryption.py /main/50 2025/08/08 21:50:09 jfsaldan Exp $
#
# cluencryption.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluencryption.py - Filesystem Encryption Framework
#
#    DESCRIPTION
#      Functionality implementation to encrypt a filesystem in the VM
#
#    NOTES
#    https://confluence.oraclecorp.com/confluence/display/EDCS/Exacloud+-+Encryption+at+Rest
#    https://confluence.oraclecorp.com/confluence/display/EDCS/ECRA-ExaCloud+Payload+for+FS+Encryption
#    https://confluence.oraclecorp.com/confluence/display/EDCS/ExaCC-Exacloud+Key-Value+DB+to+save+FS+Encryptation+Passphrase
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    08/04/25 - Bug 38268596 - EXACLOUD FEDRAMP PREVENT PROV
#                           PROBLEM | FS_ENCRYPTION FILE SHREDDING FAILS
#                           CAUSING INSTALL CLUSTERS TO FAIL
#    jfsaldan    04/21/25 - Bug 37856850 - EXACLOUD ENCRYPTION AT REST | ENSURE
#                           CLEANUP OF RESIDUAL FILES IN EXACLOUD IF PREVIOUS
#                           ATTEMPT FAILED
#    jfsaldan    10/24/24 - Bug 37209747 - EXACC:BB:CS: CREATE SERVICE FAILED
#                           AT POSTVMINSTALL - DOMU REBOOT FAILS AFTER CHANNEL
#                           SETUP
#    ririgoye    10/23/24 - Bug 37197710 - Receive mSearchExaKmsEntries result
#                           as list for ExaKVDB instances
#    jfsaldan    10/11/24 - Bug 37160121 - EXACC:OC5:PROVISIONING FAILED AT
#                           POSTVMINSTALL WITH ERROR: COULD NOT PARSE IMAGE
#                           SIZE FROM PAYLOAD
#    jfsaldan    10/07/24 - Bug 37137285 - EXACLOUD EXACC FS ENCRYPTION -
#                           ACCIDENTAL PASSPHRASE LEAKED IN EXAWATCHER LOGS
#    jfsaldan    10/04/24 - Bug 37080869 - EXACC:BB:VM: SSH TO VM IS FAILING-
#                           SSH: CONNECT TO HOST SCAQAU07DV0603.US.ORACLE.COM
#                           PORT 22: CONNECTION REFUSED
#    jfsaldan    08/23/24 - Bug 36974914 - EXACLOUD - ADD COMPUTE U01
#                           ENCRYPTION FAILS IF AHF IS RUNNING IN U01 FS
#    jfsaldan    07/19/24 - Enh 36776061 - EXACS EXACLOUD OL8 FS ENCRYPTION :
#                           ADD SUPPORT TO RESIZE AN ENCRYPTED U01 DISK
#    jfsaldan    07/02/24 - Enh 36711025 - EXACLOUD OL8 FS ENCRYPTION --
#                           EXACLOUD TO SUPPORT CREATING U01 ENCRYPTED ON THE
#                           DOMU
#    jfsaldan    06/27/24 - Bug 36624871 - EXACS:OL8 ENCRYPTION:23.4.1.2.4:
#                           FILESYSTEM RESIZE FAILING IN INVOKE EXACLOUD FOR
#                           RESHAPE OPERATION
#    jfsaldan    05/09/24 - Bug 36427983 - FORTIFY ISSUE: PASSWORD MANAGEMENT:
#                           HARDCODED PASSWORD CLUENCRYPTION.PY
#    jfsaldan    04/12/24 - Bug 36501551 - EXACLOUD - EXACC - BATCH OF PENDING
#                           CREATE SERVICE ISSUES REPORTED DURING E2E TESTING
#                           W/ FS ENCRYPTION ENABLED
#    pbellary    04/07/24 - Enh 35976881 - EXACC - SUPPORT FS ENCRYPTION AT REST 
#                         - EXACLOUD SEND METRICS FOR FAILURES (OR SUCCESS) DURING VM FS API KEY BEING INVOKED 
#    ririgoye    03/12/24 - Enh 35761667 - Added new passphrase rotation
#                           operation
#    pbellary    02/20/24 - Bug 36312160 - NODE RECOVERY : SOME RPMS ARE MISSING UNDER /U02 ON VM RESTORED FROM VM BACKUP
#    jfsaldan    02/19/24 - Enh 35951447 - EXACC - SUPPORT FS ENCRYPTION AT
#                           REST - EXACLOUD MUST INJECT KEYS VIA SOCATIO FOR
#                           ANY OPERATION THAT REQUIRES REBOOT
#    aypaul      02/15/24 - ENH#36243242 Support for exacc to store/retrieve
#                            passphrase in ExaKMS DB.
#    ririgoye    10/19/23 - Bug 35419881 - Added parallelization wrapper for FS
#                           encryption
#    hcheon      08/30/23 - 35197827 Use OCI instance metadata v2
#    jfsaldan    08/29/23 - Bug 35734737 - EXACLOUD IS MISSING LOGIC TO CREATE
#                           A SECRET FROM SCRATCH IN SIV AS LUKS PASSPHRASE
#    jfsaldan    08/18/23 - Bug 35719818 - PLEASE PROVIDE A WAY TO IDENTIFY
#                           FROM A XEN DOM0 IF THE GUESTVM HAS LUKS ENABLED OR
#                           NOT
#    jfsaldan    08/14/23 - Bug 35419066 - PREVM-SETUP - RECREATE LUKS
#                           PASSPHRASE SUPPORT FOR UNDO/RETRY OR RE-ADD SAME
#                           NODE BEFORE PRIOR SECRET PURGE
#    pbellary    08/09/23 - Bug 35683467 - VM CONSOLE - ENCRYPTION AT EXACLOUD FOR 
#                           HISTORY CONSOLE NEEDS TO USE A COMMON PATTERN TO BE USED IN CP 
#    jfsaldan    07/24/23 - Bug 35444299 - EXACS:22.2.1:DROP5:FS ENCRYPTION
#                           ENABLED:DELETE SERVICE NOT DELETING THE
#                           CORRESPONDING SECRET(S) FROM THE VAULT
#    gparada     07/10/23 - 35529689 Refactor sysimghandler.hasDomUCustomOS
#    jfsaldan    05/25/23 - Bug 35418776 - RETRY OF ENCRYPTION FAILS ON XEN FOR
#                           U02
#    jfsaldan    05/23/23 - Bug 35410783 - EXACLOUD FAILED TO CALCULATE THE NON
#                           ENCRYPTED FIRST BOOT IMAGE
#    jfsaldan    05/12/23 - Enh 35355004 - EXACLOUD - FS ENCRYPTION - CREATE
#                           DOMU ENCRYPTION PASSPHRASE WITH TAG TO SUPPORT IAM
#                           WITH 1 VAULT
#    jfsaldan    04/13/23 - Bug 35148981 - EXACS:22.2.1:DROP2:230224.1626:FS
#                           ENCRYPTION:KVM:ADB-D PROVISIONING FAILING AT
#                           POSTGINID STEP:EXACLOUD : ADB END CREATE SERVICE
#                           STEP SCRIPT ERROR
#    jfsaldan    03/07/23 - 35148981: KVM:ADB-D PROVISIONING FAILING, u02 HAS
#                           INCORRECT OWNERSHIP/PERMISSIONS
#    jfsaldan    03/03/23 - Bug 35144841 - Delete Node and then add again
#                           issue, keyapi in Dom0 is not overriden with new
#                           values
#    jfsaldan    10/13/22 - Bug 34697688 - Keyapi fails to read RegionInfo from
#                           cavium causing error during encryption
#    jfsaldan    09/14/22 - Bug 34527636 - Ebtables causes connectivity
#                           issues to fetch remote passphrase from domU
#    jfsaldan    09/13/22 - Bug 34595514 - Change u02 zipfile creation staging
#                           dir /EXAVMIMAGES/ExtraImgs/
#    jfsaldan    07/07/22 - Bug 34334376 - Add secret_name to config file and
#                           write certificates in shell wrapper on R1
#    jfsaldan    07/05/22 - Bug 34334376 - Shell Wrapper not exiting with
#                           keyapi exit-code
#    jfsaldan    05/27/22 - Bug 34219873 - DELETE KEYAPI SHELL WRAPPER FROM
#                           DOM0 DURING DELETE SERVICE
#    alsepulv    05/26/22 - Bug 33590245: Add start/stop CRS resources
#    jfsaldan    05/18/22 - Enh 34185907 - Add support to use local passphrase
#                           in DEV/QA environments only
#    jfsaldan    04/25/22 - Bug 34082448 - Add support to encrypt /u02 with
#                           OEDA
#    jfsaldan    03/17/22 - Bug 33131402 - Adding OEDA based encryption support
#    jfsaldan    02/09/22 - Enh 32941940 - FETCH ORACLE MANAGED ENCRYPTION KEYS
#                           FROM KMS VAULTS
#    alsepulv    10/07/21 - Added node_cmd_abs_path_check for lvs commands
#    jfsaldan    08/27/20 - Creation
#

import uuid
import base64
import datetime
import json
import os
import re
import csv
import glob
import difflib
from ipaddress import IPv4Address, ip_interface, ip_network
import string
import shutil
import time
from six import ensure_str
from typing import NamedTuple, Optional, Tuple
import time
import random
import tempfile
import secrets
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from exabox.exakms.ExaKmsKVDB import ExaKmsKVDB
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, ExitCodeBehavior
from exabox.core.Node import exaBoxNode
from exabox.core.Mask import mask, umask
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd_check, node_exec_cmd)

from exabox.utils.common import version_compare
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn, ebLogCritical
from exabox.ovm.clumisc import mGetDom0sImagesListSorted
from exabox.ovm.cludomufilesystems import (expand_domu_filesystem, MIB,
    ebDomUFilesystem, ebDomUFSResizeMode,shutdown_domu, start_domu)
from exabox.ovm.sysimghandler import hasDomUCustomOS
from exabox.exaoci.connectors.DefaultConnector import DefaultConnector
from exabox.exaoci.connectors.R1Connector import R1Connector
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory

from exabox.ovm.cluexaccsecrets import ebExaCCSecrets
from exabox.tools.ebOedacli.ebOedacli import ebOedacli
from exabox.kms.crypt import cryptographyAES
from oci.object_storage import ObjectStorageClient
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from oci.key_management import KmsCryptoClient
from oci.key_management.models import GenerateKeyDetails
from oci.vault import VaultsClient, VaultsClientCompositeOperations
from oci.secrets import SecretsClient
from oci.secrets.models import SecretBundle
from oci.vault.models import (CreateSecretDetails, UpdateSecretDetails,
        ScheduleSecretDeletionDetails, ScheduleSecretVersionDeletionDetails,
        Base64SecretContentDetails)
from oci.vault.models.secret_summary import SecretSummary
from cryptography.hazmat.primitives.serialization import load_ssh_public_key, load_ssh_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Constants
MSDOS   = "msdos"
GPT     = "gpt"

class MountPointInfo(NamedTuple):
    """
    Useful information to hold about a mount point
    """
    is_luks: bool
    block_device: str
    fs_type: str
    fs_label: Optional[str]
    luks_device: Optional[str]
    mount_point: str


def getMountPointInfo(aNode: exaBoxNode, aMountPoint: str)-> MountPointInfo:
    """
    This function takes a mount point and returns a NAMEDTUPLE MountPointInfo,
    which will contain important information about the specified mount point

    :param aMountPoint: a String representing the mount point from which
        information is wanted, Ex: "/u01"
    :param aNode: an already connected exaBoxNode

    :returns aMountPointInfo: a NamedTuple with information about aMountPoint:
        (is_luks, block_device, fs_label, fs_type, luks_device, mount_point)

    :raises ExacloudRuntimeError: if an error occurs while fetching information
    """

    # Declare variables
    _bin_lsblk = node_cmd_abs_path_check(aNode, "lsblk")
    _bin_findmnt = node_cmd_abs_path_check(aNode, "findmnt")

    # Get block device, FS type, and FS label
    _cmd = f"{_bin_findmnt} -rno source,fstype,label {aMountPoint}"
    _out_findmnt = node_exec_cmd_check(aNode, _cmd)
    _block_device, _fs_type, *_fs_label = _out_findmnt.stdout.strip().split()

    # the mount point might not have a label, in which case '_fs_label'
    # will be an empty list
    _fs_label = _fs_label[0] if _fs_label else ""

    # Check if block device is crypt type
    _cmd = f"{_bin_lsblk} -rno TYPE {_block_device}"
    ebLogTrace(_cmd)
    _out_block_tpye = node_exec_cmd_check(aNode, _cmd)
    _block_device_type = _out_block_tpye.stdout.strip()

    # Get mounpoint
    _cmd = f"{_bin_findmnt} -rno target {aMountPoint}"
    _out_findmnt = node_exec_cmd_check(aNode, _cmd)
    _mountpoint = _out_findmnt.stdout.strip()

    _is_luks = False
    _luks_device = ""
    if _block_device_type == "crypt":

        _is_luks = True

        # If yes, fetch underlying LUKS device
        # n: no headings
        # p: full path of devices
        # l: list like output
        # s: inverse order, to get device under _block_device, or luks device in pos 1
        # o: option NAME
        _cmd = f"{_bin_lsblk} -nprso NAME {_block_device}"
        ebLogTrace(_cmd)
        _out_list_devices = node_exec_cmd_check(aNode, _cmd)
        _block_device_tree = _out_list_devices.stdout.strip().splitlines()
        ebLogTrace(_block_device_tree)

        _luks_device = _block_device_tree[1]

    return MountPointInfo(_is_luks, _block_device, _fs_type, _fs_label,
            _luks_device, _mountpoint)

def isEncryptionRequested(aOptions:dict, aComponent: str,
        aTarget: str = "") -> bool:
    """
    Function to parse payload and check if encryption is requested by ECRA

    This confluence contains more info about the Payload sent by ECRA
    https://confluence.oraclecorp.com/confluence/display/EDCS/ECRA-ExaCloud+Payload+for+FS+Encryption

    Below is an example of how the fs_encryption part of the payload will
    look like:

    "fs_encryption": {
        "kms_id": kms_id,
        "kms_key_endpoint": kms_key_endpoint,
        "bucket_name": bucket_name,
        "bucket_namespace": bucket_namespace,
        "bucket_id": bucket_id,
        "customer_tenancy_name": customer_tenancy_name,
        "customer_tenancy_id": customer_tenancy_id,
        "secret_compartment_id": secret_compartment_id,
        "vault_id" vault_id,
        "infraComponent": [
            {
                "encryption_mode": "enabled | disabled",
                "infra_component": "dom0",
                "key_source": "KMS | SIV"
            },
            {
                "encryption_mode": "enabled | disabled",
                "infra_component": "domU",
                "key_source": "KMS | SIV"
            },
            {
                "encryption_mode": "enabled | disabled",
                "infra_component": "cell",
                "key_source": "KMS | SIV"
            }
        ]
    }

    The encryption request is determined by taking the infraComponent list in
    the payload. Then, it finds the component provided in aComponent and checks
    if the encryption mode is enabled for it. If aTarget is specified, it also
    checks if it is part of the target filesystems in the component.

    :param aOptions: dictionary representing the aOptions object
    :param aComponent: String representing the node type (dom0, domU or cell)
    :param aTarget: String representing the mountpoint to encrypt.

    :returns bool: True if encryption is requested, False otherwise
    """

    # NOTE: this can be improved if we call parseEncryption payload and just check
    # in there if encryption was requested, by extending parseEncryption function

    if aOptions.jsonconf:

        # ExaCC Check
        # If 'fs_encryption' is a string, we return False and let the ExaCC handler
        # check if this is indeed valid payload for exacc
        if aOptions.jsonconf.get("fs_encryption", None):
            if isinstance(
                    aOptions.jsonconf.get("fs_encryption"), str):
                return False

        infra_component_list = aOptions.jsonconf.get(
                "fs_encryption", {}).get("infraComponent", [])

        # If Mountpoint is not specified, just check at least 1 infra component
        # has encryption_mode=enabled
        for node_type in infra_component_list:
            if (node_type.get("infra_component", "").upper() == aComponent.upper()
                    and node_type.get("encryption_mode", "").upper() == "ENABLED"):

                # If aTarget is not provided, just check aComponent is enabled
                if not aTarget:
                    return True

                # If aTarget is provided, check that it is in enabled mode
                if aTarget in node_type.get("target_filesystems", ""):
                    return True
    return False

def createLocalFSKey(aNode:exaBoxNode, aKeyFile:str=None) -> str:
    """
    Create random pass
    This method was originally intended to be used when we encrypted
    XEN based Exadatas u01 and u02 LVs/Disks

    This is intended to be used only in dev/dbqa, we have 2 flags protecting
    this code in exabox.conf, in addition to the ECRA payload driven
    properties that define if encryption must be applied or not

    :param aNode: an already connected exaBoxNode where the key is going to be generated

    :returns string: the key file path where the key is present in the host to which
        aNode is connected
    """

    # NOTE
    # This function is now deprecated. We have no plans to encrypt XEN Exadatas
    # as of 23.1.x image version
    # We will raise an error in here in case this flow is ever called
    # We will remove this code appropiately in the upcoming future
    _force_flag = "force_xen_fsencryption"
    if get_gcontext().mGetConfigOptions().get(
            _force_flag, "False").upper() == "TRUE":
        _msg = ("This flow is now deprecated. Exacloud should not create a local "
            "passphrase. This operation will continue without generating any "
            f"passphrase, as requested by exabox.conf flag {_force_flag}")
        ebLogWarn(_msg)
        return ""

    _err = ("This flow is now deprecated. Exacloud should not create a local "
        "passphrase. The FS Encryption flow needs to follow the Cross Tenancy "
        "Authentication path to SiV to retrieve the passphrase")
    ebLogError(_err)
    raise ExacloudRuntimeError(0x96, 0x0A, _err)


def resizeEncryptedVolume(aDomU: str, aMountPoint:str) -> None:
    """
    This function perform resizing on top of the luks volume

    :param aDomU: String representing the domU FQDN
    :param aMountPoint: String representing the mountoint

    :returns None:
    """

    ebLogInfo(f"Attempting to resize Luks Volume and Filesystem on {aMountPoint} for {aDomU}")

    with connect_to_host(aDomU, get_gcontext()) as _node:

        # Get info about aMountPoint
        _mount_info  = getMountPointInfo(_node, aMountPoint)

        # Check Filesystem on aMountPoint is indeed encrypted
        if _mount_info.is_luks:

            # Get KeyApi location in node
            # https://confluence.oraclecorp.com/confluence/display/EDCS/FETCH+ORACLE+MANAGED+ENCRYPTION+KEYS+FROM+KMS+VAULTS
            # To print passphrase to stdin:
            # $ keyapi fetch -i $config_file
            _bin_keyapi, _keyapi_config, _keyapi_certs = pushAndReturnKeyApi(
                aNode = _node,
                aSecretName = _node.mGetHostname())

            # Use stdin as keyfile on cryptsetup
            _keyfile = "-"

            # If a certificate is needed, we must set the variable SSL_CERT_FILE
            # to make the keyapi use that certificate
            # https://pkg.go.dev/crypto/x509#pkg-variables
            _certs_set_cmd = ":"
            _certs_unset_cmd = ":"
            if _keyapi_certs:
                ebLogInfo(f"Using certificate file {_keyapi_certs} for resizing {aMountPoint} "
                    f"in {aDomU}")
                _certs_set_cmd = f'export SSL_CERT_FILE="{_keyapi_certs}"'
                _certs_unset_cmd = "unset SSL_CERT_FILE"

            # Resize luks volume
            _bin_cryptsetup = node_cmd_abs_path_check(_node, "cryptsetup", sbin=True)
            _cmd = (f"{_bin_cryptsetup} resize {_mount_info.block_device} "
                f"--key-file={_keyfile}")
            _cmd = f"{_bin_keyapi} fetch -i {_keyapi_config } | {_cmd}"

            # Add cert variables to keyapi cmd
            # NOTE: Make sure the exit code of the below command is the exit code of the keyapi
            _cmd = f"{_certs_set_cmd}; {_cmd}; rc=$?; {_certs_unset_cmd}; [ $rc -eq 0 ]"

            ebLogTrace(_cmd)
            node_exec_cmd_check(_node, _cmd)

            # Enlarge Filesystem to maximum capacity
            if _mount_info.fs_type == "xfs":
                _bin_xfs_growfs = node_cmd_abs_path_check(_node, "xfs_growfs", sbin=True)
                _cmd = (f"{_bin_xfs_growfs} {aMountPoint}")
                ebLogTrace(_cmd)
                node_exec_cmd_check(_node, _cmd)

            elif _mount_info.fs_type == "ext4":
                _bin_resize2fs = node_cmd_abs_path_check(_node, "resize2fs", sbin=True)
                _cmd = f"{_bin_resize2fs} {_mount_info.block_device}"
                ebLogTrace(_cmd)
                node_exec_cmd_check(_node, _cmd)

        else:
            _err_msg = f"Exacloud was expecting {aMountPoint} to be encrypted on {aDomU}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

def resizeOEDAEncryptedFS(aEbox: any, aDomU: str, aMountPoint:str):
    """
    This function performs the resize the fs mounted on aMountPoint created
    on an encrypted LUKS volume

    :param aDomU: String representing the domU FQDN
    :param aMountPoint: String representing the mountoint

    :returns None:
    """

    ebLogInfo("Attempting to resize the LUKS Volume and Filesystem on "
        f"{aMountPoint} for {aDomU}")

    with connect_to_host(aDomU, get_gcontext()) as _node:

        # Get info about aMountPoint
        _mount_info  = getMountPointInfo(_node, aMountPoint)

        # Check Filesystem on aMountPoint is indeed encrypted
        if _mount_info.is_luks:
            ebLogInfo(f"Detected an encrypted luks device on {aMountPoint} in "
                f"{aDomU}")
        else:
            _err_msg = ("Did not detect any encrypted luks volume on "
                f"{aMountPoint} in {aDomU} ")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        # Confirm LUKS keyapi is available before even start
        _keyapi_file = os.path.join("/usr/lib/dracut/modules.d/99exacrypt/",
                "VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh")
        if not _node.mFileExists(_keyapi_file):
            _err_msg = f'The keyapi script {_keyapi_file} is not present in domU'
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        try:
            _tries = 0
            _MAX_TRIES = 5
            while True:
                # Try to get keyapi data
                _out_file = None
                _out_keyapi = node_exec_cmd(_node, _keyapi_file)
                _out_file = _out_keyapi.stdout.strip()
                if _out_keyapi.exit_code!= 0:
                    _tries += 1
                    _err_msg = ('Calling keyapi command failed in domU, try '
                        f'{_tries} from {_MAX_TRIES}')
                    ebLogError(_err_msg)
                    time.sleep(5)
                else:
                    ebLogTrace(f"Success calling the keyapi in {aDomU}")
                    break
                if _tries >= _MAX_TRIES:
                    _err_msg = ('Calling keyapi command exceeded the maximum attempts '
                        f'{_MAX_TRIES} in domU {aDomU}')
                    ebLogError(_err_msg)
                    raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

            # Increase luks device to use the new maximum available
            _bin_cryptsetup = node_cmd_abs_path_check(_node, "cryptsetup",
                    sbin=True)
            _cmdstr = (f"{_bin_cryptsetup} resize {_mount_info.block_device} "
                f"--key-file={_out_file} -v")
            _out_data = node_exec_cmd(_node, _cmdstr)
            ebLogTrace(_out_data)
            if _out_data.exit_code != 0:
                _err_msg = 'cryptsetup resize command failed in domU'
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        finally:
            if _out_file and _node.mFileExists(_out_file):
                ebLogWarn(f"Deleting keyapi {_out_file}")
                node_exec_cmd(_node, f"/bin/rm -f {_out_file}")
            else:
                ebLogWarn(f"No keyapi to delete")

            # Enlarge Filesystem to maximum capacity
            ebLogInfo(f"Will now enlarge the filesystem from {aMountPoint}")
            if _mount_info.fs_type == "xfs":
                _bin_xfs_growfs = node_cmd_abs_path_check(_node, "xfs_growfs",
                    sbin=True)
                _cmd = (f"{_bin_xfs_growfs} {aMountPoint}")
                node_exec_cmd_check(_node, _cmd)

            elif _mount_info.fs_type == "ext4":
                _bin_resize2fs = node_cmd_abs_path_check(_node, "resize2fs",
                    sbin=True)
                _cmd = f"{_bin_resize2fs} {_mount_info.block_device}"
                node_exec_cmd_check(_node, _cmd)

    ebLogInfo(f"Finished resizing the encrypted layer and FS from "
            f"{aMountPoint} in {aDomU}")


def batchEncryptionSetupDomU(aCluCtrl: any, aNodes: list, aMountPoint: str) -> None:
    """
    This function acts as a parallel processing wrapper for the File System
    Encryption setup. 

    :param: aCluCtrl: exaBoxCluCtrl object
    :param: aNodes: The full list of Dom0s and DomUs where the nodes will connect to.
    :param: aMountPoint: This is the Mount Point that is desired to be encrypted,
        there are two ways to pass this parameter:
    1) Use Label syntax, which is something like LABEL=BOOT. ***This is CASE SENSITIVE***
    2) Use the mount point in which the FS is mounted, something like /u02 for example.

    :raises: ExacloudRuntimeError: If an error occurs during one of the encryption flows
    :returns: None
    """
    # Create process manager
    _maxTime = 60 * 60 * 6 # Set timeout to 6 hours per encryption process
    _plist = ProcessManager(aExitCodeBehavior=ExitCodeBehavior.IGNORE)
    _callback_list = []
    _results_map = {}
    ebLogInfo("Creating process pool for FS encryption.")
    # Submit encryption setup callbacks and store them in a list
    _start_time = datetime.datetime.now()
    for _dom0, _domU in aNodes:
        ebLogInfo(f"Added encryption process for dom0: {_dom0} and domU: {_domU}")
        _task = ProcessStructure(encryptionSetupDomU, aArgs=[aCluCtrl, _dom0, _domU, aMountPoint], aId=_domU)
        _task.mSetMaxExecutionTime(_maxTime)
        _task.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_task)
        if _task.is_alive():
            ebLogInfo(f"Encryption of domU: {_domU} is running.")
            _results_map[_task.ident] = {"domU": _domU, "dom0": _dom0, "status": "Running", "start_time": _task.mGetStartTime(), "end_time": "", "elapsed": ""}
            _callback_list.append((_task, (_dom0, _domU)))
    ebLogInfo("Running encryption setup concurrently.")
    _plist.mJoinProcess()

    # Wait for completed tasks and write to results map
    _tasks = [_task[0] for _task in _callback_list]
    _end_time = datetime.datetime.now() - _start_time
    _failed_count = 0
    for _process, _args in _callback_list:
        _dom0, _domU = _args
        _err = _process.mGetError()
        if _err:
            _results_map[_process.ident]["error"] = str(_err)
            _failed_count += 1
            ebLogError(f"Got error during domU ({_domU}) encryption: {str(_err)}.")
        else:
            ebLogInfo(f"Encryption for domU: {_domU} successful.")
        _task_start = _process.mGetStartTime()
        _task_end = _process.mGetEndTime()
        _task_elapsed = _process.mToDT(_task_end) - _process.mToDT(_task_start)
        _results_map[_process.ident]["end_time"] = _task_end
        _results_map[_process.ident]["elapsed"] = str(_task_elapsed)
        _results_map[_process.ident]["status"] = "Failed" if _results_map[_process.ident].get("error") else "Success"

    # Log the results
    ebLogInfo(f"Encryption setup ended for all {len(aNodes)} domUs. Elapsed time: {_end_time}. Errors: {_failed_count}")
    ebLogInfo(f"The results for each domU are the following:\n {json.dumps(_results_map, indent=4)}")
    # If one domU or more failed to be encrypted, raise ExacloudRuntimeError to avoid further errors
    if _failed_count >= 1:
        ebLogError("Raising exception since {_failed_count} errors were found during some processes.")
        _err_msg = f"Found errors during encryption for some domUs. Please check the result JSON."
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

def encryptionSetupDomU(aCluCtrl: any, aDom0: str, aDomU: str, aMountPoint: str) -> None:
    """
    This function performs the encryption of a Filesystem mounted on aMntPoint on
    a given aDomU

    :param: aCluCtrl: exaBoxCluCtrl object
    :param: aDom0: Dom0 host where node will connect to
    :param: aDomU: DomU host where node will connect to, in this host encryption will take place
    :param: aMountPoint: This is the Mount Point that is desired to be encrypted,
        there are two ways to pass this parameter:
    1) Use Label syntax, which is something like LABEL=BOOT. ***This is CASE SENSITIVE***
    2) Use the mount point in which the FS is mounted, something like /u02 for example.

    :raises ExacloudRuntimeError: If an error occurs during encryption flow
    :returns None:

    Steps (If any of them fail, an ExacloudRuntimeError will be raised):
    1- Check that system has completed booting up.
    2- Check that aMntPoint exists and get info about it (device path, label, type)
    3- Make sure crypt packages are installed
    4- (Optional) If filesystem type is 'xfs', resize it before unmounting it
    5- Unmount FS and any nested FS
    6- (Optional) If filesystem type is 'ext4', shrink it and commit journal
    7- Push Keyapi (Go binary on customer providioned or dummy keyapi in dev/test envs)
    8- Encrypt device
    9- Test password
    10- Open device
    11- Enlarge FS if shrunk in step 4
    12- Mount the FS and any nested FS
    13- Configure FS to mount it on reboot
    """

    ebLogInfo((f"Initiating file system encryption on FS {aMountPoint} "
               f"for domU {aDomU}"))

    with connect_to_host(aDomU, get_gcontext()) as _node:

        # Make sure system has completely booted before beginning encryption
        waitForSystemBoot(_node)

        # Fetch info about FS. Ex:
        _mount_info = getMountPointInfo(_node, aMountPoint)

        # Check Device/Filesystem on aMountPoint is not already encrypted
        # During undo/retry of WF, Exacloud does not perform decryption of FS
        # as this operation can take a lot of time. So, during a retry
        # encryption will just be a no-op if encryption has been done already

        if _mount_info.is_luks:
            _msg = (f"This is no-op, since device on {aMountPoint} is already encrypted "
                    f"on {aDomU}")
            ebLogInfo(_msg)
            return

        # Check if FS type is supported
        if not _mount_info.fs_type == "xfs" and not _mount_info.fs_type == "ext4":
            _err_msg = ("Filesystem encryption feature is only supported in "
                "filesystems formated in xfs or ext4 at the moment,"
                f"not {_mount_info.fs_type}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        # Check if packages are installed. Otherwise, try to copy and install
        # them if the appropriate exabox.conf property is set
        checkPackages(_node)

        # If encryption is called during elastic or otherwise not during CS,
        # CRS services might be running. We need to stop them before
        # unmounting the FS where it resides to prevent errors.
        _crs_started = False
        _grid_loc = aCluCtrl.mGetClusters().mGetCluster().mGetCluHome()

        if aMountPoint in _grid_loc:
            # We wait here to make sure CRS is brought up before we check for it
            time.sleep(60)
            if aCluCtrl.mCheckCrsUp(aDomU):
                ebLogInfo((f"CRS is up on {aMountPoint} in {aDomU}. "
                            "Attempting to stop it."))
                _crs_started = True
                _bin_crsctl = f"{_grid_loc}/bin/crsctl"
                _bin_kill = node_cmd_abs_path_check(_node, "kill")
                _bin_lsof = node_cmd_abs_path_check(_node, "lsof", True)

                _cmd = f"{_bin_crsctl} stop crs -f"
                ebLogTrace(_cmd)
                node_exec_cmd(_node, _cmd)

                _cmd = f"{_bin_lsof} -- {aMountPoint}"
                _out = node_exec_cmd(_node, _cmd)
                ebLogTrace(_out.stdout)

                _cmd = f"{_bin_kill} -9 $({_bin_lsof} +t -- {aMountPoint})"
                ebLogTrace(_cmd)
                node_exec_cmd_check(_node, _cmd)

        # Prepare Device/Filesystem before encryption is attempted
        prepareVolumePreEncryption(aCluCtrl, aDom0,_node, _mount_info)

        # Dumping df output just as reference in trace file
        _bin_df = node_cmd_abs_path_check(_node, "df")
        _cmd = f"{_bin_df} -h"
        _out_df = node_exec_cmd(_node, _cmd)
        ebLogTrace(_out_df.stdout)

        # Try to perform encryption on the given device. Allow '_retry_count' retries
        # Cryptsetup is smart enough to continue an incomplete encryption on some
        # circumstances. Yet, if encryption corrupts this volume completely we need to
        # recreate the VM from scratch. This retry is meant to assist if a network intermittent
        # issue doesn't allow the keyapi to be retrieved
        _retry_count = 3
        _encDevicePath = None
        while _retry_count and _encDevicePath is None:

            # Perform encryption steps using cryptsetup cli and get luks volume mapper name
            # path, e.g. /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt
            try:
                _encDevicePath = encryptNode(_node, _mount_info, aCluCtrl.mGetArgsOptions())

            # On error decrease counter by 1
            except Exception as e:
                _retry_count -=1
                ebLogError(f"An error happened while trying to encrypt {aMountPoint} "
                    f"in {aDomU}")

                # Try to close the created (if any) luks device
                closeEncryptedDevice(_node, _mount_info)

                # Raise exception if no more retries pending
                if _retry_count == 0:
                    _err_msg = ("Unable to encrypt FS, check cryptsetup stdout and stderr "
                        "on Exacloud logs. The keyapi logs to review are in "
                        f"'/opt/exacloud/fs_encryption/logging_keyapi.log' on {aDomU}. "
                        "Will try to mount back the unmounted filesystems")
                    mountNestedFS(_node, aMountPoint)
                    ebLogError(_err_msg)
                    raise ExacloudRuntimeError(0x96, 0x0A, _err_msg) from e

                # Log that a retry will be attempted
                else:


                    ebLogInfo(f"Retrying to encrypt {aMountPoint} in {aDomU}")
                    time.sleep(1)

            else:
                ebLogInfo(f'Encryption of {aMountPoint} ended succesfully. '
                    f'Running post-encryption steps in {aDomU}')

        # Prepare Device/Filesystem after encryption has been done
        prepareVolumePostEncryption(_node, _mount_info, _encDevicePath)

        # Update fstab
        updateFstab(_node, aMountPoint, _encDevicePath)

        # Remount all FS, this should use /etc/fstab to mount the newly encrypted FS
        mountNestedFS(_node, aMountPoint)

        ebLogInfo(f"Succesfully mounted {_encDevicePath} on {aMountPoint} for {aDomU}")

        # Enable systemd service
        ebLogInfo(f"Attempting to enable systemd service for {aMountPoint} on {aDomU}")
        enableSystemdService(_node, aMountPoint)

        # Dumping df output just as reference in trace file
        _cmd = f"{_bin_df} -h"
        _out_df = node_exec_cmd(_node, _cmd)
        ebLogTrace(_out_df.stdout)

        # If CRS services were running before we started encryption, we start them back up
        if _crs_started:
            _cmd = f"{_bin_crsctl} start crs -wait"
            ebLogTrace(_cmd)
            node_exec_cmd_check(_node, _cmd)


        ebLogInfo(("All encryption steps finished successfully "
                  f"for FS {aMountPoint} on domU {aDomU}"))


def prepareVolumePostEncryption(aNode: exaBoxNode, aMountPointInfo: MountPointInfo,
        aLuksMapperPath: str) -> None:
    """
    :param aNode: An already connected to a VM/Guest exaBoxNode on which to
        perform pre encryption preparation steps
    :param aMountPointInfo: a NamedTuple of MountPointInfo type containing fields:
        (is_luks, block_device, fs_label, fs_type, luks_device, mount_point)
    :param aLuksMapperPath: string representing the path on which the LUKS device
        appears open under /dev/mapper, .e.g:
        /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt
    """

    # If FS is ext4, we enlarge it now that LUKS header was added
    # and entire partition is encrypted
    if aMountPointInfo.fs_type == "ext4":
        prepareExt4FsPrePosEncryption(aNode, aLuksMapperPath, aPreEncryption=False)

    # If fstype is xfs, we check FS integrity
    elif aMountPointInfo.fs_type == "xfs":
        _bin_xfs_repair = node_cmd_abs_path_check(aNode, "xfs_repair", sbin=True)
        _cmd = f'{_bin_xfs_repair} {aLuksMapperPath}'
        node_exec_cmd_check(aNode, _cmd)

def prepareVolumePreEncryption(aCluCtrl: any, aDom0: str, aNode: exaBoxNode,
        aMountPointInfo: MountPointInfo) -> None:
    """
    This function is in charge of preparing the specified volume with its filesystem,
    within aMountPointInfo, in the host on which aNode is connected to

    :param aCluCtrl: exaBoxCluCtrl object
    :param: aDom0: Dom0 host where node will connect to, this is only required
        when encrypting an 'xfs' filesystem type
    :param aNode: An already connected to a VM/Guest exaBoxNode on which to
        perform pre encryption preparation steps
    :param aMountPointInfo: a NamedTuple of MountPointInfo type containing fields:
        (is_luks, block_device, fs_label, fs_type, luks_device, mount_point)
    """

    # If FS is of type XFS, we resize the logical volume to add space for LUKS header
    # This is done on purpose before unmounting the filesystem for XFS type
    if aMountPointInfo.fs_type == 'xfs':
        xfsResize(aCluCtrl, aDom0, aNode.mGetHostname(), aMountPointInfo.mount_point,
                aMountPointInfo.block_device)

    # Umount filesystem in aMountPoint and other filesystems mounted in a directory
    # part of aMountPoint tree
    ebLogInfo((f"Unmounting {aMountPointInfo.mount_point} recursively "
               f"on {aNode.mGetHostname()}"))
    _bin_umount = node_cmd_abs_path_check(aNode, "umount")
    _cmd = f"{_bin_umount} -R {aMountPointInfo.mount_point}"
    _out_umount = node_exec_cmd_check(aNode, _cmd)
    ebLogTrace(_out_umount.stdout)

    # If FS is ext4, we shrink it to leave space on its partition
    # for luks header, this is done after unmouting the filesystem for EXT4 tpye
    if aMountPointInfo.fs_type == "ext4":
        prepareExt4FsPrePosEncryption(aNode, aMountPointInfo.block_device,
                aPreEncryption=True)

    # Check xfs FS integrity after volume resize and FS unmount
    elif aMountPointInfo.fs_type == "xfs":
        _bin_xfs_repair = node_cmd_abs_path_check(aNode, "xfs_repair", sbin=True)
        _cmd = f'{_bin_xfs_repair} {aMountPointInfo.block_device}'
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    ebLogInfo((f"File System on {aMountPointInfo.block_device} for "
               f"{aNode.mGetHostname()} was prepared succesfuly"))

def closeEncryptedDevice(aNode: exaBoxNode, aMountPointInfo: MountPointInfo):
    """
    This function will try to use cryptsetup to close the luks
    device from _mount_info

    :param aNode: An already connected exaBoxNode on which to perform encryption
        steps
    :param aMountPointInfo: a NamedTuple of MountPointInfo type containing fields:
        (is_luks, block_device, fs_label, fs_type, luks_device, mount_point)
    :returns: None
    """

    _bin_cryptsetup = node_cmd_abs_path_check(aNode, "cryptsetup", True)
    _luks_device_name = os.path.join(
            "/dev/mapper",
            os.path.basename(f'{aMountPointInfo.block_device}-crypt'))

    _cmd = f"{_bin_cryptsetup} close {_luks_device_name}"
    ebLogTrace(_cmd)
    ebLogWarn(f"Exacloud is about to close the device: '{_luks_device_name}' "
        f"on the domU: '{aNode.mGetHostname()}'")
    _out_close = node_exec_cmd(aNode, _cmd)
    ebLogTrace(_out_close)

def encryptNode(aNode: exaBoxNode, aMountPointInfo: MountPointInfo,
        aOptions:dict) -> str:
    """
    This function handles the encryption of the volume specified within aMountPointInfo

    :param aNode: An already connected exaBoxNode on which to perform encryption
        steps
    :param aMountPointInfo: a NamedTuple of MountPointInfo type containing fields:
        (is_luks, block_device, fs_label, fs_type, luks_device, mount_point)
    :param aOptions: an aOptions context

    :returns: a string representing the path of the encrypted device as it appears open
        in /dev/mapper
    """

    # Declare LUKS device name, its mapping device in /dev/mapper and label if it exists
    _luks_device_name = os.path.basename(f'{aMountPointInfo.block_device}-crypt')
    _luks_mapper_path = f'/dev/mapper/{_luks_device_name}'
    _luks_label = f'{aMountPointInfo.fs_label}-crypt' if aMountPointInfo.fs_label else ''

    # Create keyapi and config file to VM filesystem if not already present
    # and get its remote path
    # https://confluence.oraclecorp.com/confluence/display/EDCS/FETCH+ORACLE+MANAGED+ENCRYPTION+KEYS+FROM+KMS+VAULTS
    # To print passphrase to stdin:
    # $ keyapi fetch -i $config_file
    _bin_keyapi, _keyapi_config, _keyapi_certs = pushAndReturnKeyApi(
        aNode = aNode,
        aSecretName = aNode.mGetHostname(),
        aOptions = aOptions)

    # _bin_keyapi, when executed, should output the passphrase as stdout
    # Use keyapi stdout as crtypsetup stdin
    _keyfile = "-"

    # If a certificate is needed, we must set the variable SSL_CERT_FILE
    # to make the keyapi use that certificate
    # https://pkg.go.dev/crypto/x509#pkg-variables
    _certs_set_cmd = ":"
    _certs_unset_cmd = ":"
    if _keyapi_certs:
        ebLogInfo(f"Using certificate file {_keyapi_certs} for encrypting "
            f"{aMountPointInfo.mount_point} in {aNode.mGetHostname()}")
        _certs_set_cmd = f'export SSL_CERT_FILE="{_keyapi_certs}"'
        _certs_unset_cmd = "unset SSL_CERT_FILE"

    ebLogInfo((f"Beginning FS encryption in {aNode.mGetHostname()}, "
                "this operation may take a while..."))

    # Filesystem Encryption Steps
    _bin_cryptsetup = node_cmd_abs_path_check(aNode, "cryptsetup", sbin=True)
    _cmd = (f"{_bin_cryptsetup} reencrypt --encrypt {aMountPointInfo.block_device} --type luks2 "
        f"--reduce-device-size 8192S --key-file={_keyfile}")
    _cmd = f"{_bin_keyapi} fetch -i {_keyapi_config} | {_cmd}"

    # Add cert variables to keyapi cmd
    # NOTE: Make sure the exit code of the below command is the exit code of the keyapi
    _cmd = f"{_certs_set_cmd}; {_cmd}; rc=$?; {_certs_unset_cmd}; [ $rc -eq 0 ]"
    ebLogTrace(_cmd)
    node_exec_cmd_check(aNode, _cmd)

    # Test the key file as passphrase
    ebLogInfo(f"Testing passphrase on {aMountPointInfo.block_device}")

    _cmd = (f"{_bin_cryptsetup} open --type luks2 --test-passphrase "
        f"--key-file={_keyfile} {aMountPointInfo.block_device}")
    _cmd = f"{_bin_keyapi} fetch -i {_keyapi_config} | {_cmd}"

    # Add cert variables to keyapi cmd
    # NOTE: Make sure the exit code of the below command is the exit code of the keyapi
    _cmd = f"{_certs_set_cmd}; {_cmd}; rc=$?; {_certs_unset_cmd}; [ $rc -eq 0 ]"
    ebLogTrace(_cmd)
    node_exec_cmd_check(aNode, _cmd)

    # Add label config to encrypted FS if original volume had a label
    if _luks_label:
        ebLogInfo(f"Configuring label {_luks_label} on {aMountPointInfo.block_device}")
        _cmd = f"{_bin_cryptsetup} config {aMountPointInfo.block_device} --label {_luks_label}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    # Open the encrypted device and create a mapped device
    ebLogInfo(f"Attempting to open device {aMountPointInfo.block_device}")
    _cmd = (f"{_bin_cryptsetup} open --type luks2 --key-file={_keyfile} "
        f"{aMountPointInfo.block_device} {_luks_device_name}")
    _cmd = f"{_bin_keyapi} fetch -i {_keyapi_config} | {_cmd}"

    # Add cert variables to keyapi cmd
    # NOTE: Make sure the exit code of the below command is the exit code of the keyapi
    _cmd = f"{_certs_set_cmd}; {_cmd}; rc=$?; {_certs_unset_cmd}; [ $rc -eq 0 ]"
    ebLogTrace(_cmd)
    node_exec_cmd_check(aNode, _cmd)

    return _luks_mapper_path

def mountNestedFS(aNode: exaBoxNode, aMountpoint: str) -> None:
    """
    This function should mount back the FS that where unmounted to perform
    the fs encryption.
    This assumes that file /etc/fstab already contains changes to mount
    encrypted fs.

    The way in which this is accomplished is by executing "mount -a" to mount
    any fs not already mounted from /etc/fstab.

    There is a case, in which Exacloud could have previously unmounted more
    than 1 filesystem to perform the encryption, when 1 filesystem was
    mounted on a mountpoint belonging to another filesystem.

    And, if the order in which they are listed in /etc/fstab causes one
    filesystem to fail to mount because a mountpoint doesn't already exists

    To handle this case, in this function we check exit-code of "mount -a",
    which from the man, if is 64 means some filesystems where mounted, but not
    all of them. So Exacloud will retry for N times, N being the number of times
    the aMountPoint appears in /etc/fstab

    :param aNode: An already connected exaBoxNode on which to mount aMountPoint
    :param aMountPoint: A string representing the fs that wants to be remounted

    :raise ExacloudRuntimeError: if unable to mount all fs in /etc/fstab

    :returns None:
    """

    _fstab = "/etc/fstab"

    # Check how many occurrences exist for aMountpoint in /etc/fstab
    _bin_grep = node_cmd_abs_path_check(aNode, "grep")
    _cmd = f'{_bin_grep} "{aMountpoint}" {_fstab} -c'
    _out_count = node_exec_cmd_check(aNode, _cmd, log_stdout_on_error=True)
    _count_fs = int(_out_count.stdout.strip())

    ebLogInfo(f"Ocurrences for {aMountpoint} are: {_count_fs}")

    # If no occurence, raise exception. Should not be the case unless somehow
    # we override /etc/fstab in an invalid way in a previous step
    if _count_fs == 0:
        _err_msg = (f"Didn't find any occurence of {aMountpoint} in {_fstab} "
                    f"at {aNode.mGetHostname()}")
        ebLogError(_err_msg)
        ebLogTrace(_out_count.stdout)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    # Attempt _count_fs times to mount back all fs from /etc/fstab
    # If mount -a returns 64, keep trying for _count_fs times
    _bin_mount = node_cmd_abs_path_check(aNode, "mount")
    while _count_fs != 0:
        _cmd = f"{_bin_mount} -av"
        _out_remount = node_exec_cmd(aNode, _cmd)
        ebLogTrace(_out_remount.stdout)

        # 64 means some fs where not mounted, given the order in /etc/fstab
        if _out_remount.exit_code == 64:
            _count_fs -= 1

        # Exit-code non zero is error
        elif _out_remount.exit_code:
            _err_msg = f"Unable to remount FS, check {_fstab} on {aNode.mGetHostname()}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        # If mount -a exits with 0, all filesystems where mounted
        elif not _out_remount.exit_code:
            break

    else:
        # If it was attempted _count_fs times and still mount -a was not able to
        # mount all filesystem, raise an exception
        _err_msg = (f"Failed to mount Filesystem {aMountpoint} or a filesystem "
                    "depending on it")
        _action_msg = (f"Please verify {_fstab} is valid on "
                       f"{aNode.mGetHostname()} and or review system logs to "
                       "check for root cause of what prevented the filesystem "
                       "to be mounted")
        ebLogCritical(_err_msg, _action_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

def checkPackages(aNode: exaBoxNode) -> None:
    """
    This function will make sure the required packages are installed. Specifically:
        - cryptsetup
        - cryptsetup-libs

    If cryptsetup rpms are not present in the host or do not meet the minimum version requirements,
    Exacloud will attempt to install them if the parameter "force_cryptsetup_rpm_install" is set 
    to "true" in exabox.conf

    :param aNode: an exaBoxNode already connected
    :raises ExacloudRuntimeError: If an error occurs while attempting to check if
        rpm's are present or when attempting to install them.
    :returns None:
    """

    ebLogInfo(f'Making sure cryptsetup packages are installed on {aNode.mGetHostname()}')

    # Query required rpm's on the Host, to check if already installed
    _bin_rpm = node_cmd_abs_path_check(aNode, "rpm")

    # Don't fail if command not successful, as we may attempt to install them afterwards
    _out_cryptsetup = node_exec_cmd(aNode, f"{_bin_rpm} -q cryptsetup",
            log_error=True)
    _out_cryptsetup_libs = node_exec_cmd(aNode, f"{_bin_rpm} -q cryptsetup-libs",
            log_error=True)

    # Regex to match rpm's, version is not checked here
    # NOTE, review if feasable to use rpm -q <rpm> --queryformat "{$VERSION}"
    _cryptsetup_rpm = re.search(r'cryptsetup-([\d\.-]+)\.el7\.x86_64',
            _out_cryptsetup.stdout)
    _cryptsetup_libs_rpm = re.search(r'cryptsetup-libs-([\d\.-]+)\.el7\.x86_64',
            _out_cryptsetup_libs.stdout)

    # Check if rpm's are present from above regex and make sure version is above 2.3
    if (_cryptsetup_rpm and _cryptsetup_rpm.group(1) > "2.3"
        and _cryptsetup_libs_rpm and _cryptsetup_libs_rpm.group(1) > "2.3"):

        ebLogInfo(f"Cryptsetup packages are installed on {aNode.mGetHostname()}")

    # If any of the required packages are not installed AND if the field in exabox.conf
    # "force_cryptsetup_rpm_install" is to "true", attempt to install cryptsetup rpm's
    elif get_gcontext().mGetConfigOptions().get(
            "force_cryptsetup_rpm_install", "False").upper() == "TRUE":

        ebLogWarn(f"Cryptsetup packages are not installed in {aNode.mGetHostname()}, "
            "attempting to copy and install them")
        _local_cryptsetup_rpm = os.path.join("images", "cryptsetup.x86_64.rpm")
        _local_cryptsetup_libs_rpm = os.path.join("images", "cryptsetup-libs.x86_64.rpm")

        # Make sure rpm's are present under specified directory in
        # exacloud/images
        if (not os.path.exists(_local_cryptsetup_rpm)
             or not os.path.exists(_local_cryptsetup_libs_rpm)):
            _err_msg = (f"Cryptsetup rpm's are not present at {aNode.mGetHostname()} "
                        "in local images directory. Expecting them under: "
                        f"{_local_cryptsetup_rpm} and {_local_cryptsetup_libs_rpm}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        # Copy cryptsetup-libs rpm and attempt to install it
        _remote_rpm_location = os.path.join("/tmp",
                os.path.basename(_local_cryptsetup_libs_rpm))
        aNode.mCopyFile(_local_cryptsetup_libs_rpm, _remote_rpm_location)
        _cmd = f"{_bin_rpm} -ivh --force {_remote_rpm_location}"
        ebLogTrace(_cmd)
        _out_rpm = node_exec_cmd_check(aNode, _cmd, log_stdout_on_error=True)
        ebLogTrace(_out_rpm)

        # Delete rpm after installing it
        _bin_rm = node_cmd_abs_path_check(aNode, "rm")
        _cmd = f"{_bin_rm} -f {_remote_rpm_location}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

        # Copy cryptsetup rpm and attempt to install it
        _remote_rpm_location = os.path.join("/tmp",
                os.path.basename(_local_cryptsetup_rpm))
        aNode.mCopyFile(_local_cryptsetup_rpm, _remote_rpm_location)
        _cmd = f"{_bin_rpm} -ivh --force {_remote_rpm_location}"
        ebLogTrace(_cmd)
        _out_rpm = node_exec_cmd_check(aNode, _cmd, log_stdout_on_error=True)
        ebLogTrace(_out_rpm)

        # Delete rpm after installing it
        _cmd = f"{_bin_rm} -f {_remote_rpm_location}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    # Fail since required packages are not present in the system
    else:
        _err_msg = f"Cryptsetup packages are not present in {aNode.mGetHostname()}"
        _action_msg = ("Please install the rpm's manually or set "
            "\"force_cryptsetup_rpm_install\" to \"true\" in exabox.conf to "
            "instruct exacloud to attempt installation and retry operation")
        ebLogCritical(_err_msg, _action_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

def waitForSystemBoot(aNode: exaBoxNode) -> None:
    """
    This function will wait until the system boot finishes. This is useful
    when Exacloud attempts to encrypt a filesystem right after a VM has been
    rebooted. During boot time, systemd mounts the filesystems in /etc/fstab
    and this could cause a race condition, since Exacloud requires to unmount
    the filesystem to perform the encryption, and systemd may try to mount them
    back.

    By the time Exacloud is able to login to the VM, systemd might still try to
    mount some filesystems, as part of the boot process, in the background.

    :param aNode: an exaBoxNode already connected

    :returns None:
    """

    _bin_systemd_analyze = node_cmd_abs_path_check(aNode, "systemd-analyze", sbin=True)
    _cmd = f"{_bin_systemd_analyze} time"
    _rc = 1

    while _rc:
        ebLogInfo(f"Checking if system is not booting up: {aNode.mGetHostname()}")
        ebLogInfo(f"Retrying in 1 second...: {aNode.mGetHostname()}")
        time.sleep(1)
        _out_boot = node_exec_cmd(aNode, _cmd)
        _rc = _out_boot.exit_code

    ebLogInfo(f"System boot up has completed on {aNode.mGetHostname()}")

def xfsResize(aCluCtrl: any, aDom0: str, aDomU: str, aMountPoint: str,
        aBlockDevicePath: str) -> None:
    """
    Extends the volume group and logical volume on aMntPoint
    to make space for the LUKS encryption header in the device

    Parameters:
    aCluCtrl(exaBoxCluCtrl): exaBoxCluCtrl object
    aDom0: dom0 to connect
    aDomU: domU to connect
    aMountPoint: The mount point of the xfs filesystem whose partition to resize
    aBlockFile: The block device whose partition will be resized
    """

    if aMountPoint == '/u01':
        _fs = ebDomUFilesystem.U01
    elif aMountPoint == '/u02':
        _fs = ebDomUFilesystem.U02
    else:
        _err_msg = 'Filesystem currently not supported for encryption.'
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    expand_domu_filesystem(aCluCtrl, aDom0, aDomU, _fs, extra_bytes=32*MIB,
                           check_max_size=False, resize_mode=ebDomUFSResizeMode.LV_ONLY)

    ebLogInfo(f"Volume group and logical volume for {aBlockDevicePath} were "
              f"succesfully resized on {aDomU}.")

def prepareExt4FsPrePosEncryption(aNode: exaBoxNode, aBlockDevice: str,
        aPreEncryption: bool) -> None:
    """
    This function prepares an ext4 FS to be ready pre/post encryption

    PreEncryption:
        Among the steps considered to prepare the fs are:
        - Clean/Commit FS
        - Shrink FS

    PostEncryption:
        Among the steps considered to prepare the fs are:
        - Clean/Commit FS
        - Enlarge FS

    :param aNode: an already connected exaBoxNode
    :para aBlockDevice: String representing the device to shrink
    :param aPreEncryption: True if this function should execute Pre Encryption Steps
        False if this function should execute Post Encryption Steps
    """

    _bin_e2fsck = node_cmd_abs_path_check(aNode, "e2fsck", sbin=True)
    _bin_resize2fs = node_cmd_abs_path_check(aNode, "resize2fs", sbin=True)

    # Clean FS
    _cmd = f"{_bin_e2fsck} -f -p {aBlockDevice}"
    ebLogTrace(_cmd)
    node_exec_cmd_check(aNode, _cmd)

    # Shrink/Enlarge FS to add luks header
    if aPreEncryption:
        # Shrink FS to add luks header
        _cmd = f"{_bin_resize2fs} -M {aBlockDevice}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    else:
        # Enlarge FS
        _cmd = f"{_bin_resize2fs} {aBlockDevice}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

def updateFstab(aNode: exaBoxNode, aMountPoint: str, aEncDevicePath: str) -> None:
    """
    This function updates /etc/fstab so that the encrypted device
    is mounted during boot.

    In fstab, adds to each line containing aMountPoint or a submounpoint of aMounpoint,
        the _netdev and nofail mount options

    :param aNode: an already connected exaBoxNode to the Host where the service wants to
        be enabled
    :param aMountPoint: String representing the MountPoint on which to enable service
    :param aEncDevicePath: the path of the open encrypted block volume as it appears under
        /dev/mapper/<device>

    """

    # Declare variables to use
    _fstab = "/etc/fstab"
    _fs_netdev_mntopt = "_netdev"
    _fs_nofail_mntopt = "nofail"
    ebLogInfo(f"Updating {_fstab} to include {aEncDevicePath} in {aMountPoint}")

    # Read fstab to get lines mentioning aMountPoint, e.g.
    # "/dev/mapper/VGExaDb-LVDbOra1-crypt /u01 xfs  defaults 0 0"
    # "/dev/VGExaDbDisk.grid19.0.0.0.210119.img/LVDBDisk /u01/app/19.0.0.0/grid xfs defaults 0 0"
    # It's possible there are submounpoints as well
    _bin_grep = node_cmd_abs_path_check(aNode, "grep")
    _cmd = f'{_bin_grep} "{aMountPoint}" {_fstab}'
    ebLogTrace(_cmd)
    _out_grep_fstab = node_exec_cmd_check(aNode, _cmd, log_stdout_on_error=True)
    _mount_point_lines = _out_grep_fstab.stdout.strip().split()

    # Lines in fstab should have 6 fields according man fstab, this is to check each
    # line we read from fstab has exactly 6 fields
    _fstab_line_len = 6
    if len(_mount_point_lines) % _fstab_line_len  != 0 or not _mount_point_lines:
        _err_msg = (f"File {_fstab} on {aNode.mGetHostname()} does not contain "
                    f"a valid format:\n{_mount_point_lines}")
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    # Declare index for each fstab field -> man fstab
    _IDX_FS_SPEC = 0 # device
    _IDX_FS_FILE = 1 # mountpoint
    _IDX_FS_MNTOPS = 3 # mount options

    # Divide _mount_point_lines in N lists, each list being one list with a aMountPoint
    # or submountpoint in fstab
    for _idx_start in range(0, len(_mount_point_lines), _fstab_line_len):

        # Get a list of an individual line from fstab
        _mount_point_line = _mount_point_lines[_idx_start: _idx_start+_fstab_line_len]

        # Override fs_spec field of _mount_point_line to use luks device
        # This should only be applied to aMountpoint line and NOT to submountpoints
        # "/dev/mapper/VGExaDb-LVDbOra1 /u01 xfs     defaults 0 0"
        # "/dev/mapper/VGExaDb-LVDbOra1-crypt /u01 xfs     defaults 0 0"
        if _mount_point_line[_IDX_FS_FILE] == aMountPoint:
            _mount_point_line[_IDX_FS_SPEC] = aEncDevicePath

        # Override _fs_mntops field of _mount_point_line to use _netdev
        # This applies to aMountpoint AND submountpoints
        # "/dev/mapper/VGExaDb-LVDbOra1-crypt /u01 xfs     defaults 0 0"
        # becomes:
        # "/dev/mapper/VGExaDb-LVDbOra1-crypt /u01 xfs     defaults,_netdev 0 0"
        if _fs_netdev_mntopt in _mount_point_line[_IDX_FS_MNTOPS]:
            ebLogTrace(f"File {_fstab} already contains {_fs_netdev_mntopt} in "
                f"{_mount_point_line[_IDX_FS_FILE]} line")
        else:
            ebLogInfo(f"File {_fstab} doesn't contain {_fs_netdev_mntopt} in "
                f"{_mount_point_line[_IDX_FS_FILE]} line, adding it")
            _mount_point_line[_IDX_FS_MNTOPS] = \
                    f"{_mount_point_line[_IDX_FS_MNTOPS]},{_fs_netdev_mntopt}"

        # Override _fs_mntops field of _mount_point_line to use nofail
        # This applies to aMountpoint AND submountpoints
        # "/dev/mapper/VGExaDb-LVDbOra1-crypt /u01 xfs     defaults,_netdev 0 0"
        # becomes:
        # "/dev/mapper/VGExaDb-LVDbOra1-crypt /u01 xfs     defaults,_netdev,nofail 0 0"
        if _fs_nofail_mntopt in _mount_point_line[_IDX_FS_MNTOPS]:
            ebLogTrace(f"File {_fstab} already contains {_fs_nofail_mntopt} in "
                f"{_mount_point_line[_IDX_FS_FILE]} line")
        else:
            ebLogInfo(f"File {_fstab} doesn't contain {_fs_nofail_mntopt} in "
                f"{_mount_point_line[_IDX_FS_FILE]} line, adding it")
            _mount_point_line[_IDX_FS_MNTOPS] = \
                    f"{_mount_point_line[_IDX_FS_MNTOPS]},{_fs_nofail_mntopt}"


        # Convert list mount point line into string to override remote fstab
        _line_to_write = " ".join(_mount_point_line)

        # Override line in _fstab
        _bin_sed = node_cmd_abs_path_check(aNode, "sed")
        _bin_sed_option = "-E -i --follow-symlinks"
        _cmd = f'{_bin_sed} {_bin_sed_option} "s@.+{_mount_point_line[_IDX_FS_FILE]}\\s.+@{_line_to_write}@" {_fstab}'
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd, log_stdout_on_error=True)

    # This is juts to log the fstab file and have information in the logs
    _bin_cat = node_cmd_abs_path_check(aNode, "cat")
    _cmd = f"{_bin_cat} {_fstab}"
    ebLogTrace(_cmd)
    _out_cat_fstab = node_exec_cmd_check(aNode, _cmd, log_stdout_on_error=True)
    ebLogTrace(_out_cat_fstab.stdout)

    # Dump and check if mount in fake mode doesnt fail
    # Useful to review if /etc/fstab was not wrongfully edited
    # Man says use findmnt instead, but findmnt version in exadata doesn't support --verify
    _bin_mount = node_cmd_abs_path_check(aNode, "mount")
    ebLogTrace("Dumping fake mount -a")
    _cmd = f"{_bin_mount} -fva"
    _out_fake_mount = node_exec_cmd_check(aNode, _cmd,
            log_stdout_on_error=True)
    ebLogTrace(_out_fake_mount.stdout)

def enableSystemdService(aNode: exaBoxNode, aMountPoint: str) -> None:
    """
    This function will attempt to create and enable a Service in aDomU so that
    the LUKS Device mounted on aMountPoint can be unlocked during boot time.

    Steps:
    - Check if service already exists (leverage this for retry WF)
    - Copy service file
    - Add directives needed to create right dependencies for the service to be executed
        at the right moment during boot
    - Enable Service

    :param aNode: an already connected exaBoxNode to the Host where the service wants to
        be enabled
    :param aMountPoint: String representing the MountPoint on which to enable service

    :raises ExacloudRuntimeError: if an error occurs while creating/enabling the service
    """

    # Declare useful variables
    _mountpoint_dotted = aMountPoint.replace("/", "-") # e.g. '/u02' -> '-u02'
    _service_name = f"luks-dev{_mountpoint_dotted}.service" # e.g. luks-dev-u02.serivce
    _remote_service_unit_file = f"/etc/systemd/system/{_service_name}"
    _bin_systemctl = node_cmd_abs_path_check(aNode, "systemctl")

    ebLogInfo(f"Adding service {_service_name} to {aNode.mGetHostname()}")

    # Check if service is present and active in aDomU
    if aNode.mFileExists(_remote_service_unit_file):
        ebLogInfo("Service unit file is already present: "
                f"{_remote_service_unit_file}, attempting to overwrite and enable")

        _cmd = f"{_bin_systemctl} is-active {_service_name}"
        ebLogTrace(_cmd)
        _rc = node_exec_cmd(aNode, _cmd).exit_code

        # If old service is enabled, we disable it first
        ebLogInfo("Service is enabled. Attempting to disable before proceeding")
        if _rc == 0:
            _cmd = f"{_bin_systemctl} disable {_service_name}"
            node_exec_cmd(aNode, _cmd)

    else:
        ebLogInfo("Service unit file is not present: "
                f"{_remote_service_unit_file}, attempting to add and enable")

    # Modify remote service unit file to add needed directives
    _patched_service = buildRemoteUnitFile(aNode, aMountPoint)

    # Create tmp service file in Exacloud and copy it to desired Host
    with tempfile.NamedTemporaryFile(delete=True) as _tmp_service_file:
        _tmp_service_file.write(_patched_service.encode("utf-8"))
        _tmp_service_file.flush()
        aNode.mCopyFile(_tmp_service_file.name, _remote_service_unit_file)

    # Set ownership
    _bin_chown = node_cmd_abs_path_check(aNode, "chown")
    _cmd = f"{_bin_chown} root:root {_remote_service_unit_file}"
    ebLogTrace(_cmd)
    node_exec_cmd_check(aNode, _cmd)

    # Set permissions
    _bin_chmod = node_cmd_abs_path_check(aNode, "chmod")
    _cmd = f"{_bin_chmod} 600 {_remote_service_unit_file}"
    ebLogTrace(_cmd)
    node_exec_cmd_check(aNode, _cmd)

    # Enable the service
    _cmd = f"{_bin_systemctl} enable {_service_name}"
    ebLogTrace(_cmd)
    _out_disable_service = node_exec_cmd_check(aNode, _cmd)

    ebLogInfo(f"Succesfully enabled '{_service_name}' in '{aNode.mGetHostname()}'")

def buildRemoteUnitFile(aNode: exaBoxNode, aMountPoint: str) ->str:
    """
    This function contains the necesary information to patch the service unit file
    template in Exacloud, so that the service when enabled is executed by systemd
    at the right moment during boot time. The service should:
        - Fetch passphrase from Remote location
        - Open LUKS Volumes with passphrase

    These dependencies are needed because systemd must open the LUKS Volumes before it
    attempts to consume mount unit files to mount encrypted filesystems

    :param aNode: an already connected exaBoxNode to the Host where dependencies will be
        added
    :param aMountPoint: the mountpoint for which we must add dependencies, systemd should
        execute the script that opens the LUKS Volumes before mount unit files are
        consummed to mount aMountPoint or any other submounts

    :return: a string representing the service file patched with the directives needed
    """

    # Path to the local template used to generate service unit file
    # This template is written in a way so we can patch it easily using string.Template
    _local_service_unit_file = \
            "scripts/fs_encryption/fs_encryption.service.tpl"

    # Declare mapping to use when patching local service unit file
    # This dictionary should contain as keys the entries on the template files
    # that we want to patch. If template file contains '$Before', this dictionary should
    # contain 'Before' key
    _service_file_mapping = {}

    # Convert filesystem cannonical path to the format used in mount unit files
    # /u01/app/18.1.0.0/grid becomes u01-app-18.1.0.0-grid
    # Strip leading "/"
    _mount_unit = aMountPoint[1:].replace("/", "-")
    _mount_unit_file = f"{_mount_unit}.mount"

    # The operation above is dangerous, so we make sure we correctly calculated
    # the mount unit by checking if it exists on the system, i.e. something like
    # 'systemct is-active u01.mount'
    _bin_systemctl = node_cmd_abs_path_check(aNode, "systemctl")
    _cmd = f"{_bin_systemctl} is-active {_mount_unit_file}"
    ebLogTrace(_cmd)
    _out_mount_unit = node_exec_cmd_check(aNode, _cmd)

    # Once we verify that the mount unit file is correct, add the Before directive to the
    # dictionary that will be used to patch the local service file
    _service_file_mapping["Before"] = f"Before={_mount_unit_file}"

    # Add command on service unit file that will fetch passphrase and unlock devices
    # The command should be placed in '[Service]' section, it should look something like:
    # ExecStart=sh -c 'keyapi | cryptsetup open <device> <mapped-open-device> --key-file=-'
    # Where keyapi is an only root owned executable script that prints to stdout the
    # passhprase, which is passed as stdin on cryptsetup to open the Luks Device

    # Get KeyApi and config file paths
    _bin_keyapi, _keyapi_config, _keyapi_certs = pushAndReturnKeyApi(
        aNode = aNode,
        aSecretName = aNode.mGetHostname())

    # Get information about aMountPoint, needed to create cryptsetup command to open
    # luks device during boot time
    _mount_info = getMountPointInfo(aNode, aMountPoint)
    ebLogTrace(f"Mountpoint info about {aMountPoint}: {_mount_info}")
    _luks_device = _mount_info.luks_device
    _luks_mapping = os.path.basename(_mount_info.block_device)

    # If a certificate is needed, we must set the variable SSL_CERT_FILE
    # to make the keyapi use that certificate
    # https://pkg.go.dev/crypto/x509#pkg-variables
    _certs_set_cmd = ":"
    _certs_unset_cmd = ":"
    if _keyapi_certs:
        ebLogInfo(f"Using certificate file {_keyapi_certs} in service unit file "
            f"{_mount_info.mount_point} in {aNode.mGetHostname()}")
        _certs_set_cmd = f'export SSL_CERT_FILE="{_keyapi_certs}"'
        _certs_unset_cmd = "unset SSL_CERT_FILE"

    # This is the command systemd will execute when running our service unit file
    # In essence, we want _bin_keyapi to print the pasphrase to stdout and to use that
    # as stdin for cryptsetup
    _bin_cryptsetup = node_cmd_abs_path_check(aNode, "cryptsetup", sbin=True)
    _cmd = (f"{_bin_keyapi} fetch -i {_keyapi_config} | {_bin_cryptsetup} open "
        f"{_luks_device} {_luks_mapping} --key-file=-")

    # Add cert variables to keyapi cmd
    # NOTE: Make sure the exit code of the below command is the exit code of the keyapi
    _cmd = f"{_certs_set_cmd}; {_cmd}; rc=$?; {_certs_unset_cmd}; [ $rc -eq 0 ]"
    ebLogTrace(f"Patching service unit file for '{_mount_info.mount_point}' "
            f"with command: {_cmd}")

    # Add the directive ExecStart in the dictionary used to patch service file
    _cmd_sh_wrapper = f"/bin/sh -c '{_cmd}'"
    _service_file_mapping["ExecStart"] = f"ExecStart={_cmd_sh_wrapper}"

    # Use _service_file_mapping to patch the Template Service Unit File
    ebLogInfo(f"Attempting to patch service template '{_local_service_unit_file}', "
            f"using: '{_service_file_mapping}' directives")

    with open(_local_service_unit_file, 'r') as _local_file:
        _template = string.Template(_local_file.read())
        _service_file_patched = _template.substitute(_service_file_mapping)

    ebLogTrace("Succesfully patched service file template, result is:\n"
        f"{_service_file_patched}")

    return _service_file_patched


def pushAndReturnNonOedaLocalKeyapi(aNode: exaBoxNode) -> Tuple[str]:
    """
    This function copies the keyapi used in R1/dev environments
    This is an alternative to the Go binary to test in environments
        where resource principals doesn't work

    :param aNode: an already connected exaBoxNode

    :returns: a tuple with three elements:
        + String representing the full path where keyapi exists in the host where
          aNode is connected
        + an empty String representing the full path where the config file would be
          in a real non DEV environment
        + an empty String representing the full path where the certs file would be
          in a real non DEV environment
    """

    # Declare paths
    _local_keyapi_path = "scripts/fs_encryption/fs_encryption_key_api.sh"
    _remote_keyapi_path = "/opt/exacloud/fs_encryption/keyapi"

    # If keyapi doesn't exists, copy it and set proper permissions and ownership
    if not aNode.mFileExists(_remote_keyapi_path):

        ##
        ## Below is only for dev testing, we use a passphrase in the filesystem
        ## instead of storing the passphrase remotely
        ##

        # Get Key File location
        _key_path = createLocalFSKey(aNode)

        _key_file_mapping = {
            "pass_file": f"pass_file={_key_path}"
            }

        # Patch _local_key_api template with desired key_path
        with open(_local_keyapi_path, 'r') as _local_file:
            _template = string.Template(_local_file.read())
            _keyapi_patched = _template.substitute(_key_file_mapping)

        ebLogTrace(f"Keyapi template patch result is:\n{_keyapi_patched}")

        # Make sure Directory exists before copying keyapi
        _bin_mkdir = node_cmd_abs_path_check(aNode, "mkdir")
        _directory = os.path.dirname(_remote_keyapi_path)
        _cmd = f"{_bin_mkdir} -p {_directory} "
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

        # Create tmp keyapi and copy it to desired Host
        with tempfile.NamedTemporaryFile(delete=True) as _tmp_keyapi:
            _tmp_keyapi.write(_keyapi_patched.encode("utf-8"))
            _tmp_keyapi.flush()
            aNode.mCopyFile(_tmp_keyapi.name, _remote_keyapi_path)

        # Set ownership
        _bin_chown = node_cmd_abs_path_check(aNode, "chown")
        _cmd = f"{_bin_chown} root:root {_remote_keyapi_path}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

        # Set permissions
        _bin_chmod = node_cmd_abs_path_check(aNode, "chmod")
        _cmd = f"{_bin_chmod} 500 {_remote_keyapi_path}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    return _remote_keyapi_path, "", ""


def pushAndReturnKeyApi(aNode: exaBoxNode,
        aSecretName: str,
        aOptions: Optional[dict] = {},
        ) -> Tuple[str]:
    """
    This function receives an already connected aNode and will check if it already
    contains the keyapi and config file needed to fetch the passphrase from a secure
    remote location.

    If the node doesn't contain the keyapi this function will copy it.
    If the node doesn't contain the config file this funciton will attempt to create
        and copy it. The config file is build from the aOptions object, so if the
        caller expects to create a config file it should pass an aOptions object.
    If the caller expects the file to be already present an aOptions can not be
        passed, e.g. during luks resize

    Else this is a no-op and just returns the remote path of keyapi and its config file

    :param aNode: an already connected exaBoxNode
    :param aSecretName: a String representing the secret name to write in the
       config file that the keyapi will use, this name will be the domU FQDN
    :param aOptions[Optional]: an aOptions object

    :raises ExacloudRuntimeError: if an error occurs

    :returns: a tuple with two elements:
        + String representing the full path where keyapi exists in the host where
          aNode is connected
        + String representing the full path where the config file exists in the
          host where aNode is connected
        + [Optional] String representing the full path where the certs file exists
          in the host where aNode is connected
    """

    # Use local dummy passphrase if dev/qa environment detected and required
    # property is present in exabox.conf
    if useLocalPassphrase():
        ebLogInfo(f"{aNode.mGetHostname()}: Using local keyapi instead of remote SiV one")
        return pushAndReturnNonOedaLocalKeyapi(aNode)

    # Declare paths
    _local_keyapi_path = "packages/keyapi"
    _remote_keyapi_path = "/opt/exacloud/fs_encryption/keyapi"
    _remote_config_file = os.path.join(os.path.dirname(_remote_keyapi_path), "config_file")
    _remote_certs_file = ""

    # Declare certs variable if applicable

    # In R1 we must make sure we copy the mission control cert to use
    # it when the keyapi is called
    if mIsR1():
        ebLogTrace(f"R1 env detected, will copy R1 certs to {aNode.mGetHostname()}")
        _local_certs_file = "exabox/kms/combined_r1.crt"
        _remote_certs_file = os.path.join(os.path.dirname(_remote_keyapi_path), "certs_file")

    # If keyapi doesn't exists, copy it and set proper permissions and ownership
    if not aNode.mFileExists(_remote_keyapi_path):

        ebLogInfo(f"Copying fsencryption keyapi to '{_remote_keyapi_path}', "
            f"domU is: {aNode.mGetHostname()}")
        # Make sure Directory exists before copying keyapi
        _bin_mkdir = node_cmd_abs_path_check(aNode, "mkdir")
        _directory = os.path.dirname(_remote_keyapi_path)
        _cmd = f"{_bin_mkdir} -p {_directory} "
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

        # Copy Go binary to remote directory
        aNode.mCopyFile(_local_keyapi_path, _remote_keyapi_path)

        # Set ownership go binary
        _bin_chown = node_cmd_abs_path_check(aNode, "chown")
        _cmd = f"{_bin_chown} root:root {_remote_keyapi_path}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

        # Set permissions go binary
        _bin_chmod = node_cmd_abs_path_check(aNode, "chmod")
        _cmd = f"{_bin_chmod} 500 {_remote_keyapi_path}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    else:
        ebLogInfo(f"A keyapi is already present under '{_remote_keyapi_path}', "
            f"this is a no-op, domU is: {aNode.mGetHostname()}")

    # Make sure the certificate file is copied to aNode if a certificate
    # is needed
    if _remote_certs_file:

        if not aNode.mFileExists(_remote_certs_file):
            ebLogInfo(f"Copying certs file '{_local_certs_file}' "
                f"to {aNode.mGetHostname()}")

            # Copy cert file
            aNode.mCopyFile(_local_certs_file, _remote_certs_file)

            # Set ownership certs file
            _bin_chown = node_cmd_abs_path_check(aNode, "chown")
            _cmd = f"{_bin_chown} root:root {_remote_certs_file}"
            ebLogTrace(_cmd)
            node_exec_cmd_check(aNode, _cmd)

            # Set permissions certs file
            _bin_chmod = node_cmd_abs_path_check(aNode, "chmod")
            _cmd = f"{_bin_chmod} 500 {_remote_certs_file}"
            ebLogTrace(_cmd)
            node_exec_cmd_check(aNode, _cmd)

        else:
            ebLogInfo(f"Certs file '{_remote_certs_file}' "
                f"already present in {aNode.mGetHostname()}")

    # If config file doesn't exists, try to create, copy and set proper permissions
    # and ownership.
    if not aNode.mFileExists(_remote_config_file):

        # To create a config file, an aOptions should be passed, callers who dont pass an
        # aOptions expect the config file to be already created and present under 
        # _remote_keyapi_path in aNode. Raise exception if not present
        if not aOptions:
            _err_msg = ("Exacloud expected an aOptions object to be passed for "
                f"{aNode.mGetHostname()}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg)

        ebLogInfo(f"Copying config file '{_local_certs_file}' "
            f"to {aNode.mGetHostname()}")
        # Create config file in Exacloud and copy it to desired Host
        _remote_resources = parseEncryptionPayload(aOptions, "domU")

        _remote_config = dict()
        _remote_config["vault_ocid"] = _remote_resources.vault_ocid
        _remote_config["hostname"] = aSecretName

        with tempfile.NamedTemporaryFile(delete=True, mode='w') as _tmp_config_file:
            _tmp_config_file.write(json.dumps(_remote_config))
            _tmp_config_file.flush()
            aNode.mCopyFile(_tmp_config_file.name, _remote_config_file)

        # Set ownership config file
        _bin_chown = node_cmd_abs_path_check(aNode, "chown")
        _cmd = f"{_bin_chown} root:root {_remote_config_file}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

        # Set permissions config file
        _bin_chmod = node_cmd_abs_path_check(aNode, "chmod")
        _cmd = f"{_bin_chmod} 500 {_remote_config_file}"
        ebLogTrace(_cmd)
        node_exec_cmd_check(aNode, _cmd)

    else:
        ebLogInfo(f"A config file is present under '{_remote_config_file}', "
            f"this is no-op it, domU is: {aNode.mGetHostname()}")

    return _remote_keyapi_path, _remote_config_file, _remote_certs_file

class RemoteOciResources(NamedTuple):
    """
    Useful information to hold about a remote passphrase
    The information in here should be sufficient to generate a request
    against OCI services to fetch and decrypt the remote passphrase

    A tuple of this type may hold KMS or SiV parameters depending on the key_source
    requested by ECRA
    """
    kms_ocid: str                           # KMS/ObjectStorage and SiV
    kms_crypto_endpoint: Optional[str]      # KMS/ObjectStorage
    bucket_name: Optional[str]              # KMS/ObjectStorage
    bucket_namespace: Optional[str]         # KMS/ObjectStorage
    vault_ocid: Optional[str]               # SiV
    secret_compartment_ocid: Optional[str]  # SiV
    key_source: str                         # SiV
    cloud_vmcluster_ocid: str               # SiV

def parseEncryptionPayload(aOptions: dict, aComponent: str)-> RemoteOciResources:
    """
    This function parses the payload looking for encryption related entries

    :param aComponent: a string representing the component for which parsing is required
        e.g. domU|cell|dom0
    :param aOptions: aOptions object/dictionary with global config

    :returns RemoteOciResources: a NamedTuple containing information to retrieve the
        remote passphrase
    """

    # Declare Variable needed
    _json = aOptions.jsonconf
    _json_encrypt = _json.get("fs_encryption", {})
    _json_component_list = _json_encrypt.get("infraComponent", [])

    # Get Key source from ecra payload
    for _node_type in _json_component_list:

        if _node_type.get("infra_component", "").upper() == aComponent.upper():

            if _node_type.get("key_source", "").upper() == "SIV":
                _key_source = "SIV"
                break

            elif _node_type.get("key_source", "").upper() == "KMS":
                _key_source = "KMS"
                break

            else:
                _err_msg = (f"Exacloud failed to parse payload, invalid key source "
                    f"present:\n {json.dumps(_json_encrypt)}")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg)


    # Create NamedTuple with the information from the payload
    _remote_passphrase_info = RemoteOciResources(
        kms_ocid = _json_encrypt.get("kms_id", ""),
        kms_crypto_endpoint = _json_encrypt.get("kms_key_endpoint", ""),
        bucket_name = _json_encrypt.get("bucket_name", ""),
        bucket_namespace =_json_encrypt.get("bucket_namespace", ""),
        vault_ocid =_json_encrypt.get("vault_id", ""),
        secret_compartment_ocid = _json_encrypt.get("secret_compartment_id", ""),
        cloud_vmcluster_ocid = _json_encrypt.get("cloud_vmcluster_id", ""),
        key_source = _key_source,
    )

    return _remote_passphrase_info

def generateObjectData(aDEKCiphertext:str, aDEKPlainText:str) -> str:
    """
    This function generates a random pasphrase using ebExaCCSecrets.mGeneratePassKey(),
    this passphrase is then encrypted using aDEKPlainText. The function returns a string
    with information about the passphrase.

    :param aDEKCipherText: String Representing DEK Ciphertext to be used
    :param aDEKPlainText: String representing DEK Plaintext to be used to encrypt data

    :returns: a String in json format with following fields:
        encDEK: String representing Ciphertext
        encData: String representingthe password to be used to encrypt/open/closing the
                luks volumes. This password was encrypted using the aDEKPlainText. The
                generation of the random password is done using
                ebExaCCSecrets.mGeneratePassKey()
        Example of returned string:
            '{
                "encDEK": "IW0UlcZJfQ79ACeoRIvL7ClsgYjacdUsBm9cJim6qsYcOtcGEpIP5emyQmWQJEg/gvn+kGy+7qrdZqtDAJaGclyzXh0o+AAAAAA=",
                "encData": "U2FsdGVkX1/hHIODrgWNYzS6QVX5lQOQqnMJKU1yFwl2Xryz413c2l2fLIY//hpT\nn2jYdlfGn6/KXutX+/43qA=="
            }'
    """

    # Generate random password
    _exacc_secrets = ebExaCCSecrets("")
    _password = _exacc_secrets.mGeneratePassKey().encode("utf-8")
    _b64_pass = base64.b64encode(_password)

    # Initialize crypto object, this is used to perform encryption on raw password
    _crypto_aes = cryptographyAES()
    _encdata = _crypto_aes.mEncrypt(aDEKPlainText, _b64_pass).decode("utf-8")

    # Build dictionary and return as a string in json format
    _object_data = {}
    _object_data["encDEK"] = aDEKCiphertext
    _object_data["encData"] = _encdata

    # Important to use json and not dict, as when we fetching the key from the
    # remote location we use the json package in Go binary
    _json_string = json.dumps(_object_data)

    return _json_string

def mIsR1():
    """
    This function returns True if R1 env is detected
    It checks in link local address of Cavium for the occurrence of 'sea'
    """

    _r1 = False
    _url = 'http://169.254.169.254/opc/v2/instance/region'
    _header = {'Authorization': 'Bearer Oracle'}
    try:
        _resp = ensure_str(urlopen(Request(_url, None, _header)).read())
    except HTTPError as e:
        ebLogInfo('The server couldn\'t fulfill the request.')
        ebLogInfo('Error code: ', e.code)
    except URLError as e:
            ebLogInfo('Reason: ', e.reason)
    else:
        if 'sea' in _resp:
            _r1 = True
    return _r1

class OCIClients(NamedTuple):
    """
    This NamedTuple holds the required OCI Clients needed to perform requests against
    an OCI service(s).

    Depending on key_source the clients created will differ
    """

    object_storage_client: Optional[ObjectStorageClient]
    kms_crypto_client: Optional[KmsCryptoClient]
    generate_key_details: Optional[GenerateKeyDetails]
    vault_client: Optional[VaultsClient]
    secrets_client: Optional[SecretsClient]

def createKMSClients(aKMSCryptoEndpoint: str, aKMSKeyId: str) -> OCIClients:
    """
    This is the logic to create the clients used to push the remote passphrase
    in Object Storage.

    :param aKMSCryptoEndpoint: string representing the crypto endpoint to use with
        a master key with ocid aKMSKeyId
    :param aKMSKeyId: string representing the ocid of the master key to use
        for crypto operations

    :returns OCIClients: a named tuple containing the clients created
    """
    
    # Initialize Instance Principals, ObjectStorageClient and KmsCryptoClient
    _factory = ExaOCIFactory()
    _object_storage_client = _factory.get_object_storage_client()
    _kms_crypto_client = None
    
    # Declare KMS Crypto Client if aKMSCryptoEndpoint is not ""
    if aKMSCryptoEndpoint != "":
        _kms_crypto_client = _factory.get_crypto_client(aKMSCryptoEndpoint)
        ebLogTrace("KMS Crypto Client created")
    else:
        _kms_crypto_client = None
        ebLogTrace("KMS Crypto Client not created, DS/undo flow")

    # Create GenerateKeyDetails object
    # This one doesn't need any endpoint,certificates
    if aKMSKeyId != "":
        # Required variable for GenerateKeyDetails
        DEFAULT_KEY_LENGTH = 32
        DEFAULT_KEY_ALGORITHM = "AES"
        _key_shape = {"algorithm": DEFAULT_KEY_ALGORITHM, "length": DEFAULT_KEY_LENGTH}
        _gkd = GenerateKeyDetails()
        _gkd.key_id = aKMSKeyId
        _gkd.include_plaintext_key = True
        _gkd.key_shape = _key_shape
    else:
        _gdk = None
        ebLogTrace("Key Details not created, DS flow")

    return OCIClients(
            object_storage_client = _object_storage_client,
            kms_crypto_client = _kms_crypto_client,
            generate_key_details = _gkd,
            vault_client = None,
            secrets_client = None)

def createVaultClients() -> OCIClients:
    """
    This function creates a Vault Client used to handle secrets

    :returns OCIClients: a named tuple containing the clients created
    """

    # Initialize Instance Principals and SecretsClient
    _factory = ExaOCIFactory()
    _vault_client = _factory.get_vault_client()
    _secrets_client = _factory.get_secrets_client()

    return OCIClients(
            object_storage_client = None,
            kms_crypto_client = None,
            generate_key_details = None,
            vault_client = _vault_client,
            secrets_client = _secrets_client)

def createOCIClientsSetup(aRemoteOciResourcesTuple: RemoteOciResources) -> OCIClients:
    """
    This function is in charge of initializing the needed clients
    to push the passphrase to the remote location

    :param aRemoteOciResourcesTuple: a NamedTuple containing:
            kms_ocid: Optional[str]
            kms_crypto_endpoint: Optional[str]
            bucket_name: Optional[str]
            bucket_namespace: Optional[str]
            vault_ocid: Optional[str]
            key_source: str

    :raises ExacloudRuntimeError: If some error occurrs. Be careful and DON'T MASK
        original error if the exception happened while attempting to create a client

    :returns OCIClients: a NamedTuple containing the clients created
    """

    # Maximum number of re attempts allowed
    _retries = 5
    ebLogInfo(f"Attempting to create OCI Clients, attempting '{_retries}' times")

    for n in range(_retries):
        ebLogTrace(f"Attempt number: {n} to create OCI Clients")
        try:
            if aRemoteOciResourcesTuple.key_source.upper() == "SIV":
                _oci_clients = createVaultClients()

            elif aRemoteOciResourcesTuple.key_source.upper() == "KMS":
                _oci_clients = createKMSClients(
                    aKMSCryptoEndpoint = aRemoteOciResourcesTuple.kms_crypto_endpoint,
                    aKMSKeyId = aRemoteOciResourcesTuple.kms_ocid
                    )

        except Exception as e:
            ebLogWarn("An error has occured while attempting to create OCI Clients, "
                    f"the error is:\n {e}")
            time.sleep(5)

        # OCI Clients created succesfuly, break for loop
        else:
            ebLogInfo("OCI Clients have been created successfuly")
            break

    # Raise exception if Exacloud failed to create clients
    else:
        _err_msg = ("Exacloud was unable to create OCI Clients needed to push "
            "and encrypt the passphrase used for encryption of luks devices")
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg)

    return _oci_clients

def checkRemotePassphraseNotPresent(aOCIClientsTuple: OCIClients, aDomU: str,
        aRemoteOciResourcesTuple: RemoteOciResources, aDelete: bool)-> None:
    """
    This function will check if a remote passphrase is present in a bucket or vault
    specified in aRemoteOciResourcesTuple

    If a passphrase is found to exists, depending on aDelete this function will:
        aDelete(True): attempt to delete the remote passphrase
        aDelete(False): raise an ExacloudRuntimeError

    :param aOCIClientsTuple: a tuple with the OCI Clients to use
    :param aDomU: String representing the domU for which we want to check if a passphrase
        exists. The object name to search is the domU name
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    """

    if aRemoteOciResourcesTuple.key_source == "SIV":
        checkRemotePassphraseNotPresentSiV(
            aOCIClientsTuple = aOCIClientsTuple,
            aDomU = aDomU,
            aRemoteOciResourcesTuple = aRemoteOciResourcesTuple,
            aDelete = aDelete)

    else:
        raise NotImplementedError("Exacloud FS Encryption only support's 'SIV' "
                "key_source, please retry the operation using SIV")

def checkRemotePassphraseNotPresentSiV(aOCIClientsTuple: OCIClients, aDomU: str,
        aRemoteOciResourcesTuple: RemoteOciResources, aDelete: bool) -> None:
    """
    This function will use the aSecretsClient to check in the vault if a secret with
    aDomU name exists. The vault is read from aRemoteOciResourcesTuple.

    If a passphrase is found to exists, depending on aDelete this function will:
        aDelete(True): attempt to delete the remote passphrase
        aDelete(False): raise an ExacloudRuntimeError

    :param aOCIClientsTuple: a tuple with the OCI Clients to use
    :param aDomU: String representing the domU for which we want to check if a passphrase
        exists. The object name to search is the domU name
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored

    :raises ExacloudRuntimeError:
    """

    ebLogInfo(f"Checking if secret is present for: {aDomU}")
    ebLogTrace(f"Using vault: '{aRemoteOciResourcesTuple.vault_ocid}'")

    # To review if a passphrase exists we use the SecretsClient get_secret_bundle_by_name
    # method, this method raises an exception if unable to locate the specified
    # object(in this case the domU name)
    try:
        _secret_bundle = aOCIClientsTuple.secrets_client.get_secret_bundle_by_name(
            secret_name = aDomU,
            vault_id = aRemoteOciResourcesTuple.vault_ocid)

    except Exception as e:
        ebLogInfo(f"No passphrase/secret present for {aDomU}, continuing. Error: {e}")
    else:
        _msg = (f"A key has been found for {aDomU}, "
                f"vault_id={aRemoteOciResourcesTuple.vault_ocid}, "
                f"secret name={aDomU}")

        # If a passphrase exists and aDelete is True, attempt to delete it
        if aDelete:
            ebLogWarn(_msg)
            deleteRemotePassphraseSiV(
                    aVaultClient = aOCIClientsTuple.vault_client,
                    aRemoteOciResourcesTuple = aRemoteOciResourcesTuple,
                    aDomU = aDomU,
                    aSecretBundle = _secret_bundle)

        # If a passphrase exists and aDelete is False, raise an exception
        else:
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0121, 0x0A, _msg)

def getRemoteSecret(aVaultClient: VaultsClient,
        aRemoteOciResourcesTuple: RemoteOciResources,
        aSecretName) -> SecretSummary:
    """
    This function will check if a remote passphrase is present in a vault
    specified in aRemoteOciResourcesTuple and will return an object
    representing it if so.


    :param aVaultClient: a vault client already initiated
    :param aDomU: String representing the domU for which we want to check if a passphrase
        exists. The object name to search is the domU name
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :returns : a Secret object if a passphrase is found to exists, this function
        will return it, otherwise it will return None
    """

    ebLogInfo(f"Checking if secret exists with name: {aSecretName}")
    ebLogTrace(f"Using vault: '{aRemoteOciResourcesTuple.vault_ocid}'")

    # To review if a passphrase exists we use the SecretsClient get_secret_bundle_by_name
    # method, this method raises an exception if unable to locate the specified
    # object(in this case the domU name)
    _secret_obj = None
    try:
        _secret_bundle = aVaultClient.list_secrets(
            compartment_id = aRemoteOciResourcesTuple.secret_compartment_ocid,
            name = aSecretName,
            vault_id = aRemoteOciResourcesTuple.vault_ocid)

    except Exception as e:
        ebLogInfo(f"No passphrase/secret present for {aSecretName}, "
                f"continuing. Error: {e}")

    else:
        if len(_secret_bundle.data) != 0:
            ebLogInfo(f"A key has been found for {aSecretName}, "
                f"vault_id={aRemoteOciResourcesTuple.vault_ocid}, "
                f"compartment_id={aRemoteOciResourcesTuple.secret_compartment_ocid}")
            _secret_obj = _secret_bundle.data[0]

    return _secret_obj


def cancelSecretDeletion(aVaultClient: VaultsClient,
        aRemoteOciResourcesTuple: RemoteOciResources,
        aSecretBundle) -> None:
    """
    This function attempts to cancel the deletion of a secret with name aSecretName
    under the Vault specified in aOCIClientsTuple

    :param aVaultClient: a vault client already initiated
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :param aSecretBundle: an object representing the secret, the secret will have the
        same name as the domU to which it belongs

    :raises ExacloudRuntimeError: If some error occurrs while attempting to cancel the
        deletion of the secret
    """

    ebLogInfo(f"Attempting to cancel the deletion of the remote luks passphrase from "
        f"'{aSecretBundle.secret_name}'")

    # Attempt to cancel secret deletion, we will add a small sleep because we want
    # to avoid continuing past this point if the secret is in a
    # transisioning state, e.g. 'SCHEDULING DELETION' instead of 'PENDING_DELETION'
    try:
        _response = aVaultClient.cancel_secret_deletion(
            secret_id = aSecretBundle.id)
        time.sleep(5)

    except Exception as e:
        _err_msg = ("An error has occurred while attempting to cancel the deletion of "
                f"the luks passphrase from '{aSecretBundle.secret_name}', "
                f"error is:\n {e}")
        ebLogError(_err_msg)
        ebLogTrace(f"OCI resources used:\n {aRemoteOciResourcesTuple}")
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e

    # Log success message and response ids
    else:
        _msg = ("The remote luks passphrase scheduled deletion has been canceled "
            f"for vm {aSecretBundle.secret_name}, with id {aSecretBundle.id}")
        ebLogInfo(_msg)
        ebLogTrace(_response.request_id)


def deleteRemotePassphraseSiV(aVaultClient: VaultsClient,
        aRemoteOciResourcesTuple: RemoteOciResources, aDomU: str,
        aSecretBundle) -> None:
    """
    This function attempts to delete an object with aDomU name from the bucket and
    bucket namespace specified in aOCIClientsTuple

    :param aVaultClient: a vault client already initiated
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :param aDomU: String representing the domU FQDN, the object to upload will have the
        same name as the domU to which it belongs

    :raises ExacloudRuntimeError: If some error occurrs while attempting to delete
        the passphrase from the remote bucket
    """

    ebLogInfo(f"Attempting to delete the remote luks passphrase from '{aDomU}'")

    # We need secret id to delete secret
    _secret_id = aSecretBundle.data.secret_id

    # Calculate time of deletion
    _today = datetime.datetime.now()
    _delta = datetime.timedelta(days = 5)

    _deletion_date = _today + _delta
    _deletion_date_formatted = _deletion_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Create schedule secret deletion object needed to schedule deletion
    _secret_deletion_details = ScheduleSecretDeletionDetails(
            time_of_deletion = _deletion_date_formatted
            )

    # Attempt to schedule deletion, we will add a small sleep because we want
    # to avoid continuing past this point if the secret is in a
    # transisioning state, e.g. 'SCHEDULING DELETION' instead of 'PENDING_DELETION'
    try:
        _response = aVaultClient.schedule_secret_deletion(
            secret_id = _secret_id,
            schedule_secret_deletion_details = _secret_deletion_details)
        time.sleep(5)

    except Exception as e:
        _err_msg = ("An error has occurred while attempting to delete the remote luks "
                f"passphrase from '{aDomU}', error is:\n {e}")
        ebLogError(_err_msg)
        ebLogTrace(f"OCI resources used:\n {aRemoteOciResourcesTuple}")
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e

    # Log success message and response ids
    else:
        _msg = ("The remote luks passphrase has been scheduled for deletion for "
                f"vm {aDomU}, with secret_id {_secret_id}, and deletion time of "
                f"{_deletion_date_formatted} "
                f"secret for VM '{aDomU}'")
        ebLogInfo(_msg)
        ebLogTrace(_response.request_id)


def deleteRemotePassphraseKMS(aObjectStorageClient: ObjectStorageClient,
        aRemoteOciResourcesTuple: RemoteOciResources, aDomU: str) -> None:
    """
    This function attempts to delete an object with aDomU name from the bucket and
    bucket namespace specified in aOCIClientsTuple

    :param aObjectStorageClient: an object storage client already initiated
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :param aDomU: String representing the domU FQDN, the object to upload will have the
        same name as the domU to which it belongs

    :raises ExacloudRuntimeError: If some error occurrs while attempting to delete
        the passphrase from the remote bucket
    """

    ebLogInfo(f"Attempting to delete the remote luks passphrase from '{aDomU}'")

    try:
        aObjectStorageClient.delete_object(
            namespace_name=aRemoteOciResourcesTuple.bucket_namespace,
            bucket_name=aRemoteOciResourcesTuple.bucket_name,
            object_name=aDomU)
    except Exception as e:
        _err_msg = ("An error has occurred while attempting to delete the remote luks "
                f"passphrase from '{aDomU}'")
        ebLogError(_err_msg)
        ebLogTrace(f"OCI resources used:\n {aRemoteOciResourcesTuple}")
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e

    else:
        _msg = (f"The remote luks passphrase has been deleted for {aDomU}, "
                f"bucket name={aRemoteOciResourcesTuple.bucket_name}, "
                f"bucket_namespace={aRemoteOciResourcesTuple.bucket_namespace}, "
                f"object name={aDomU}")
        ebLogInfo(_msg)

def deleteRemotePassphraseSetup(aOptions:dict, aDomuList:list) -> None:
    """
    This function will attempt to delete the remot passphrase used to open
    the luks devices for each domU from aDomUList

    :param aOptions: dictionary representing the aOptions object
    :param aDomuList: a list with the domu for which a passphrase want's to be created

    :returns: None
    :raises ExacloudRuntimeError: If this functions detects a passphrase exists for a
        given domU from aDomUList and is unable to delete it
    """

    # Get information from payload about the OCI resources to be used to store/encrypt
    # the passphrase
    _remote_oci_resources = parseEncryptionPayload(aOptions, "domU")

    # Attempt to initialize the required OCI Client
    _oci_clients = createOCIClientsSetup(aRemoteOciResourcesTuple = _remote_oci_resources)

    # Check if a passphrase exists for each domU from aDomUList, if a passphrase
    # exists, attmpet to delete it
    for _domU in aDomuList:
        checkRemotePassphraseNotPresent(
            aOCIClientsTuple = _oci_clients,
            aDomU = _domU,
            aRemoteOciResourcesTuple = _remote_oci_resources,
            aDelete = True)

def deleteSecretVersion(aOCIClientsTuple: OCIClients, 
        aRemoteOciResourcesTuple: dict, aSecretVersion: SecretBundle):
    """
    Deletes a particular secret version based on its' name.

    :param aOCIClientsTuple: a NamedTuple containing the OCI Client needed to perform
        the crypto and objec storage operations
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :param aSecretVersion: The version of the secret to delete
    """

    # Check if deletion is feasible
    _vault_client = aOCIClientsTuple.vault_client
    _current_versions = _vault_client.list_secret_versions(aSecretVersion.secret_id).data
    if not len(_current_versions) > 1:
        ebLogWarn("Cannot delete secret version since there's one or less versions.")
        return

    # Retrieve current state of secret version
    _secrets_client = aOCIClientsTuple.secrets_client
    _current_version = _secrets_client.get_secret_bundle(
        aSecretVersion.secret_id,
        version_number=aSecretVersion.version_number,
        secret_version_name=aSecretVersion.version_name
    ).data

    if "CURRENT" in _current_version.stages:
        ebLogError("Cannot delete secret version since it's the current version.")
        return

    # Create secret deletion details
    _today = datetime.datetime.now()
    _delta = datetime.timedelta(minutes=5)

    _deletion_date = _today + _delta
    _deletion_date_formatted = _deletion_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    _details = ScheduleSecretVersionDeletionDetails(
        time_of_deletion=_deletion_date_formatted
    )

    # Delete retrieved bundle
    _response = None
    try:
        _response = _vault_client.schedule_secret_version_deletion(
            _current_version.secret_id,
            _current_version.version_number,
            _details
        )
    except Exception as e:
        _err_msg = f"Could not schedule deletion of secret version. ({str(e)})"
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e

    return _response

def createAndPushRemotePassphraseKMS(aOCIClientsTuple: OCIClients,
        aRemoteOciResourcesTuple: dict, aDomU: str) -> None:
    """
    :param aOCIClientsTuple: a NamedTuple containing the OCI Client needed to perform
        the crypto and objec storage operations
    :param aDomU: String representing the domU FQDN, the object to upload will have the
        same name as the domU to which it belongs
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored

    :raises ExacloudRuntimeError: If some error occurrs while attempting to create or
        push the passphrase to the remote bucket

    """

    # Create a unique password per VM and push it to object storage
    ebLogInfo(f"Attemptiong to create passphrase to use on luks devices for {aDomU}")

    # Generate data encryption details, i.e. retreive ciphertext and plaintext using
    # kms crypto client
    _crypto_gen_dek = aOCIClientsTuple.kms_crypto_client.generate_data_encryption_key(
            generate_key_details = aOCIClientsTuple.generate_key_details)

    _ciphertext = json.loads(str(_crypto_gen_dek.data))["ciphertext"]
    _plaintext = json.loads(str(_crypto_gen_dek.data))["plaintext"]

    # Generate a random passphrase and use _plaintext to encrypt it
    _object_data = generateObjectData(_ciphertext, _plaintext)

    # Attempt to upload the information previosuly generated to the remote bucket
    # specified in aRemoteOciResourcesTuple, which includes the ciphertext and the
    # passphrase encrypted
    try:
        aOCIClientsTuple.object_storage_client.put_object(
                    namespace_name=aRemoteOciResourcesTuple.bucket_namespace,
                    bucket_name=aRemoteOciResourcesTuple.bucket_name,
                    object_name=aDomU,
                    put_object_body=_object_data)
    except Exception as e:
        _err_msg = ("An error has occured while trying to push a "
            f"filesystem encryption key for {aDomU}")
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e
    else:
        ebLogInfo(f"Pushed fs object passphrase for {aDomU}")

def createAndPushRemotePassphrase(aOCIClientsTuple: OCIClients, aDomU: str,
        aRemoteOciResourcesTuple: RemoteOciResources)-> None:
    """
    This function will create and push the passphrase to be used by a luks device,
    to the specified KMS/SiV parameters provided by ECRA
    """

    if aRemoteOciResourcesTuple.key_source == "SIV":
        createAndPushRemotePassphraseSiV(
            aOCIClientsTuple = aOCIClientsTuple,
            aRemoteOciResourcesTuple = aRemoteOciResourcesTuple,
            aDomU = aDomU)

    elif aRemoteOciResourcesTuple.key_source == "KMS":
        createAndPushRemotePassphraseKMS(
            aOCIClientsTuple = aOCIClientsTuple,
            aRemoteOciResourcesTuple = aRemoteOciResourcesTuple,
            aDomU = aDomU)

def createAndPushRemotePassphraseSiV(aOCIClientsTuple: OCIClients,
        aRemoteOciResourcesTuple: dict, aDomU: str) -> None:
    """
    This function creates and pushes a passphrase to be used by a luks device

    :param aOCIClientsTuple: a NamedTuple containing the OCI Client needed to push
        the passphrase to the remote Vault
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :param aDomU: String representing the domU FQDN, the object to upload will have the
        same name as the domU to which it belongs

    :raises ExacloudRuntimeError: If some error occurrs while attempting to create or
        push the passphrase to the remote Vault
    """
    # Create composite operations client 
    _vault_client = aOCIClientsTuple.vault_client
    _composite_client = VaultsClientCompositeOperations(_vault_client)

    # Create a unique password per VM and push it to SiV
    ebLogInfo("Attempting to create passphrase to use on luks devices for "
        f"{aDomU}")
    ebLogTrace("CloudVMCluster OCID is: "
        f"'{aRemoteOciResourcesTuple.cloud_vmcluster_ocid}'")

    _tag_namespace = "fs_encryption"
    _tag_definition = "cluster_id"

    ebLogTrace(f"Exacloud to use tag definition: '{_tag_definition}'")

    # Generate random passphrase
    _exacc_secrets = ebExaCCSecrets("")

    _password = _exacc_secrets.mGeneratePassKey().encode("utf-8")
    _b64_pass = base64.b64encode(_password).decode()

    # Create secret content needed by Secret Details object
    _secret_content = Base64SecretContentDetails(
            content_type = "BASE64",
            content = _b64_pass)

    # Create secret details needed by Vault Client to create a secret
    _secret_details = CreateSecretDetails(
            compartment_id = aRemoteOciResourcesTuple.secret_compartment_ocid,
            key_id = aRemoteOciResourcesTuple.kms_ocid,
            secret_content = _secret_content,
            secret_name = aDomU,
            vault_id = aRemoteOciResourcesTuple.vault_ocid,
            defined_tags = {
                _tag_namespace: {
                    _tag_definition: aRemoteOciResourcesTuple.cloud_vmcluster_ocid
                }
            }
        )

    # Try to push it to remote Vault
    try:
        _response = _composite_client.create_secret_and_wait_for_state(
            create_secret_details=_secret_details,
            wait_for_states=["ACTIVE"]
        )

    except Exception as e:
        _err_msg = ("An error has occured while trying to push a "
            f"filesystem encryption secret key for {aDomU}")
        _action_msg = (f"Please verify that the IAM setup is configured "
            "correctly, i.e. dynamic-groups and policies are in "
            "place to grant privileges to the VM where Exacloud is running "
            "to create secrets in the specified vault."
            f"Remote Resources tuple: {aRemoteOciResourcesTuple}")
        ebLogCritical(_err_msg, _action_msg)
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e
    else:
        ebLogInfo(f"Pushed fs secret passphrase for {aDomU}")


def createNewSecretVersion(
        aOCIClientsTuple: OCIClients,
        aRemoteOciResourcesTuple: dict,
        aSecretId: str,
        aState: str = "CURRENT") -> None:
    """
    This function creates a new Secret Version for the secret with ID aSecretId

    :param aOCIClientsTuple: a NamedTuple containing the OCI Client needed to push
        the passphrase to the remote Vault
    :param aRemoteOciResourcesTuple: a NamedTuple information about the remote location
        where the passphrase is to be stored
    :param aSecretId: a string representing the ID of the secret for which to create
        a new version
    :param aState: a string representing the state of the secret to use when creating
        the new version

    :raises ExacloudRuntimeError: If some error occurrs while attempting to create or
        push the passphrase to the remote Vault
    """

    # Create composite operations client
    _vault_client = aOCIClientsTuple.vault_client
    _composite_client = VaultsClientCompositeOperations(_vault_client)

    # Create a unique password per VM and push it to SiV
    ebLogInfo("Attempting to create new version for passphrase to use on luks devices "
        f"for {aSecretId}")
    ebLogTrace("CloudVMCluster OCID is: "
        f"'{aRemoteOciResourcesTuple.cloud_vmcluster_ocid}'")

    _tag_namespace = "fs_encryption"
    _tag_definition = "cluster_id"

    ebLogTrace(f"Exacloud to use tag definition: '{_tag_definition}'")

    # Generate random passphrase
    _exacc_secrets = ebExaCCSecrets("")

    _password = _exacc_secrets.mGeneratePassKey().encode("utf-8")
    _b64_pass = base64.b64encode(_password).decode()

    # Create secret content needed by Secret Details object
    _secret_content = Base64SecretContentDetails(
            content_type = "BASE64",
            content = _b64_pass)

    # Create the object to update the secret
    _update_secret_details = UpdateSecretDetails(
        defined_tags = {
            _tag_namespace: {
                _tag_definition:  aRemoteOciResourcesTuple.cloud_vmcluster_ocid
            }
        },
        secret_content = _secret_content
        )

    # Try to push it to remote Vault, and wait 10 seconds while it ACTIVATEs
    # We can implement the proper logic in the future to save ourselves a few seconds
    try:
        _response = _composite_client.update_secret_and_wait_for_state(
            aSecretId,
            _update_secret_details,
            wait_for_states=['ACTIVE']
        )

    except Exception as e:
        _err_msg = ("An error has occured while trying to push a new version for the "
            f"filesystem encryption secret key for {aSecretId}")
        _action_msg = (f"Please verify that the IAM setup is configured "
            "correctly, i.e. dynamic-groups and policies are in "
            "place to grant privileges to the VM where Exacloud is running "
            "to create secrets in the specified vault."
            f"Remote Resources tuple: {aRemoteOciResourcesTuple}")
        ebLogCritical(_err_msg, _action_msg)
        raise ExacloudRuntimeError(0x0121, 0x0A, _err_msg) from e
    else:
        ebLogInfo(f"Created new version for the fs secret passphrase for {_response.data.secret_name}")

def createAndPushRemotePassphraseSetup(aOptions:dict, aSecretsList:list):
    """
    Function to create a passphrase for the names from aSecretsList
    The passphrase is uploaded into the bucket and bucket_namespace specified in the
    payload.

    Uses bucketname, namespace from payload
    :param aOptions: dictionary representing the aOptions object
    :param aSecretsList: a list of secret names (for now the domu for which
        a passphrase want's to be created

    :raises ExacloudRuntimeError: if an error occurs while creating the passphrase
        or when attempting to push the passphrase to the remote location

    """

    # Get information from payload about the OCI resources to be used to store/encrypt
    # the passphrase
    _remote_oci_resources = parseEncryptionPayload(aOptions, "domU")

    # Note add check of _remote_oci_resources

    # Attempt to initialize the required OCI Client
    _oci_clients = createOCIClientsSetup(aRemoteOciResourcesTuple = _remote_oci_resources)


    # Running this step means that the VM is not created, so we're safe
    # to delete, create, recreate the SiV passphrases
    for _secret_name in aSecretsList:

        # Check if a secret exists
        _secret_obj = getRemoteSecret(
            aVaultClient = _oci_clients.vault_client,
            aSecretName = _secret_name,
            aRemoteOciResourcesTuple = _remote_oci_resources)

        # If none  exists, we create a new one
        if _secret_obj is None:

            # create new secret
            createAndPushRemotePassphraseSiV(
                aOCIClientsTuple = _oci_clients,
                aRemoteOciResourcesTuple = _remote_oci_resources,
                aDomU = _secret_name)

        # If one exists, and it SCHEDULED for DELETION, we change it's state
        # to NORMAL
        elif _secret_obj.lifecycle_state in ["PENDING_DELETION"]:

            cancelSecretDeletion(
                aVaultClient = _oci_clients.vault_client,
                aSecretBundle = _secret_obj,
                aRemoteOciResourcesTuple = _remote_oci_resources)

            # Once the secret is normal, we create a new version of the secret and return
            createNewSecretVersion(
                aOCIClientsTuple = _oci_clients,
                aRemoteOciResourcesTuple = _remote_oci_resources,
                aSecretId = _secret_obj.id,
                aState = "CURRENT")

###
### OEDA support
###

def ensureSystemFirstBootEncryptedExists(aCluCtrl: any, aDom0Name: str):
    '''
    This function ensures that the System.first.boot.<version>.encripted.img
    file needed to create a KVM Guest with FS Encryption enabled exists
    This should be a 1 time operation per dom0/System.first.boot image

    Basically this function will check in aDom0Name if a file with following,
    structure exists: System.first.boot.<version>.encripted.img, where <version>
    stand for the current EXADATA image version to use for the DomU.
    It doesn't have to be the same as the dom0 version. See bug 35410783

    :param aCluCtrl: Clucontrol object
    :param aDom0Name: String representing the KVM Host on where to ensure if the
        encrypted System First Boot image exists
    :raises ExaloudRuntimeError: if an error occurrs while attempting to generate
                    the encrypted image
    '''


    # Get exadata version that will be used to create the DomU
    _exadata_img_version = mGetDom0sImagesListSorted(aCluCtrl)[0]

    _custom_domu_img_ver: Optional[str] = hasDomUCustomOS(aCluCtrl)
    if _custom_domu_img_ver:
        _exadata_img_version = _custom_domu_img_ver

    _first_boot_dir = "/EXAVMIMAGES"

    # We expect System.first.boot image to follow the naming convention:
    # System.first.boot.<exadata version>.img
    _first_boot_image_name = os.path.join(_first_boot_dir,
            f"System.first.boot.{_exadata_img_version}.img")

    # Calculate encrypted First Boot image name, which should follow the naming:
    # System.first.boot.<exadata version>.2.10.0.0.220317.encrypted.img
    _first_boot_image_name_encrypted = os.path.join(_first_boot_dir,
            f"System.first.boot.{_exadata_img_version}.encrypted.img")

    with connect_to_host(aDom0Name, get_gcontext()) as _node:

        # Check the non encrypted System First Boot image exists
        if _node.mFileExists(_first_boot_image_name):
            ebLogInfo(f"The non encrypted first boot image {_first_boot_image_name} "
                    f"exists (as expected) in {aDom0Name}")

        # Fail if we calculated incorrectly the non encrypted image fail, as we need
        # it to create the encrypted First Boot image
        else:
            _err_msg = ("Exacloud failed to calculate the non encrypted first boot "
                f"image in {aDom0Name}, or the image was not found: {_exadata_img_version}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        # If already present this is no-op
        if _node.mFileExists(_first_boot_image_name_encrypted):
            ebLogInfo("Encrypted System First Boot image: "
                f"'{_first_boot_image_name_encrypted}' already exists")

        # Create it with vm_maker --encrypt command
        else:
            ebLogInfo(f"Encrypted System First Boot: '{_first_boot_image_name_encrypted}'"
                   f" doesn't exist on {aDom0Name}, will attempt to create it. "
                   "This operation may take a few minutes")
            _cmd = f"/opt/exadata_ovm/vm_maker --encrypt {_first_boot_image_name}"
            ebLogTrace(_cmd)
            _out_vmmaker_encrypt = node_exec_cmd_check(_node, _cmd)
            ebLogInfo(f"Encrypted System First Boot: '{_first_boot_image_name_encrypted}'"
                      f" created successfuly on {aDom0Name}")
            ebLogTrace(_out_vmmaker_encrypt.stdout)


def ensureSystemFirstBootEncryptedExistsParallelSetup(aCluCtrl: any, aDom0List: list):
    """
    This is a wrapper to run the function ensureSystemFirstBootEncryptedExists in
    parallel on aDom0List

    :param aCluCtrl: Clucontrol object
    :param aDom0List: List of Dom0s where to ensure if the encrypted System First Boot
        image exists
    """

    # Create Process Manager
    _plist = ProcessManager()

    # Create one process per Host from aDom0List and append the process to Process Manager
    for _host in aDom0List:
        ebLogInfo("Spawning process to check encrypted First Boot image exists in "
            f"{_host}")

        _p = ProcessStructure(ensureSystemFirstBootEncryptedExists,
             (aCluCtrl, _host,),)
        _p.mSetMaxExecutionTime(20*60) # 20 minutes timeout
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)

    _plist.mJoinProcess()

    # Check for timeouts
    if _plist.mGetStatus() == "killed":
        _err = "A timeout while checking encrypted first boot image existed"
        ebLogError(_err)
        ebLogTrace(_plist)
        raise ExacloudRuntimeError(0x0403, 0xA, _err)

    ebLogInfo("Finished checking Encrypted First Boot image exists")

def disableEncryptionFromXML(aCluCtrl: any, aXmlPath=None) -> None:
    """
    This function patches the XML to disable FileSystem enable on KVM
    Guests using oedacli
    This will not diable encryption on the cluster, that is a different
    OEDACLI command

    Parameters:
    :param aCluCtrl: Clucontrol object
    :param aXmlPath [Optional]: If present, we override this XML, otherwise
        we use the base XML from clucontrol

    :raise ExacloudRuntimeError: if an error occurs while performing XML patching

    Below is an example of oedacli usage to disable encryption before KVM Guest
    exists:
    For an individual guest
    oedacli> ALTER MACHINE \
             KEYAPI=''
             WHERE HOSTNAME = scaqai14adm03vm01
    oedacli> SAVE ACTION FORCE

    For all guests in a cluster
    oedacli> ALTER CLUSTER
             KEYAPI=''
             WHERE CLUSTERID=1
    oedacil> SAVE ACTION FORCE

    RESHAPE NOTE:
        I noticed while testing ADD COMPUTE that OEDA doesn't add the 'keyapi'
        tag to the new computes sections when doing running the CLONE GUEST call.
        To overcome this, we need to first disable the keyapi tag in the XML, that is
        achieved by using the same ALTER command to add a keyapi, but with an empty
        'keyapi', e.g. to disable for all the cluster
        oedacli> ALTER CLUSTER
                 KEYAPI=''
                 WHERE CLUSTERID=1
        oedacil> SAVE ACTION FORCE
        After doing this, we can then enable the encryption again.
        For now, there is no reason to not do this for every operation. So, we will
        always set an empty keyapi to sanityze the XML, and then we'll apply the
        encryption real 'keyapi' tag.

    """

    ebLogInfo("Beggining XML patching to disable FileSystem Encryption")

    # Build remote path for the keyapi and copy it to the dom0's
    _clu_id = aCluCtrl.mGetClusters().mGetCluster().mGetCluId()

    # Module ebOedaCli is used to modify the XML thorugh oedacli
    _oedacli_bin = os.path.join(aCluCtrl.mGetOedaPath(), 'oedacli')
    _oedacli = ebOedacli(_oedacli_bin, os.path.join(aCluCtrl.mGetOedaPath(), "log"),
            aLogFile="oedacli_encrypt.log")
    _oedacli.mSetAutoSaveActions(True)
    _oedacli.mSetDeploy(True)

    # Need to copy keyapi if script
    _cmd =f"ALTER CLUSTER KEYAPI='' WHERE CLUSTERID = {_clu_id}"
    _oedacli.mAppendCommand(_cmd)

    # Run commands in specified XML
    if aXmlPath:
        _xml_path = aXmlPath
    else:
        _xml_path = aCluCtrl.mGetPatchConfig()
    _cmdout = _oedacli.mRun(_xml_path, _xml_path)
    ebLogTrace(_cmdout)
    ebLogInfo(f"XML {aCluCtrl.mGetPatchConfig()} has been modified to disable encryption")


def patchXMLForEncryption(aCluCtrl: any, aXmlPath=None) -> None:
    """
    This function patches the XML to enable FileSystem encryption on KVM
    Guests using oedacli

    Parameters:
    :param aCluCtrl: Clucontrol object
    :param aXmlPath [Optional]: If present, we override this XML, otherwise
        we use the base XML from clucontrol

    :raise ExacloudRuntimeError: if an error occurs while performing XML patching

    Steps:
    Filesystem encryption is performed during the creation of the VM. It is
    performed at individual logical volume level.

    The API to perform the encryption for Exacloud is oedacli.
    There are two main different scenarios to perform encryption:
        1- The Guest doesn't exists:
            Before OEDA install.sh has been used to create the KVM Guest,
            oedacli will be used to modify the XML to set attributes for KVM
            Guest encryption. This will tell OEDa to create an encrypted Guest

        2- The Guest already exists
            oedacli updates the XML and interacts directly with KVM Host and
            Guest to add/remove encrypted volumes and to decrypt volumes
            NOTE: Encrypt all the Guest is currently not supported once it's created
    Below is an example of oedacli usage to enable encryption before KVM Guest
    exists:
    For an individual guest
    oedacli> ALTER MACHINE \
             KEYAPI='http://slc14ulr.us.oracle.com/yum/patchmgr/rkapi.sh'
             WHERE HOSTNAME = scaqai14adm03vm01
    oedacli> SAVE ACTION FORCE

    For all guests in a cluster
    oedacli> ALTER CLUSTER
             KEYAPI='http://slc14ulr.us.oracle.com/yum/patchmgr/rkapi.sh'
             WHERE CLUSTERID=1
    oedacil> SAVE ACTION FORCE

    """

    ebLogInfo("Beggining XML patching to enable FileSystem Encryption")

    # Build remote path for the keyapi and copy it to the dom0's
    _clu_id = aCluCtrl.mGetClusters().mGetCluster().mGetCluId()
    _clu_name = aCluCtrl.mGetClusters().mGetCluster().mGetCluName()
    _remote_keyapi_dir = "/opt/exacloud/fs_encryption"
    _keyapi_name = f"fs_encryption_keyapi_{_clu_name}"
    _remote_keyapi_path = os.path.join(_remote_keyapi_dir, _keyapi_name)

    # Copy the keyapi to each Dom0
    for _dom0, _domU in aCluCtrl.mReturnElasticAllDom0DomUPair():

        # KEYAPI argument should point to a script that fetches the keyfile
        # We need to patch the XML with the keyapi path to be used to fetch the remote
        # passphrase from the VM. This keyapi, if passed as a path to OEDA should be
        # copied to the Host. If passed as a URL there's no need to copy anything
        # but the keyapi should be available to OEDA in the URL specified for download
        copyOEDAKeyApiToNode(aHost = _dom0,
                aRemoteKeyapiPath = _remote_keyapi_path,
                aDomU = _domU,
                aOptions = aCluCtrl.mGetArgsOptions(),
                aIsExaCC = aCluCtrl.mIsOciEXACC())

    # Module ebOedaCli is used to modify the XML thorugh oedacli
    _oedacli_bin = os.path.join(aCluCtrl.mGetOedaPath(), 'oedacli')
    _oedacli = ebOedacli(_oedacli_bin, os.path.join(aCluCtrl.mGetOedaPath(), "log"),
            aLogFile="oedacli_encrypt.log")
    _oedacli.mSetAutoSaveActions(True)
    _oedacli.mSetDeploy(True)

    # Need to copy keyapi if script
    _cmd =f"ALTER CLUSTER KEYAPI='{_remote_keyapi_path}' WHERE CLUSTERID = {_clu_id}"
    _oedacli.mAppendCommand(_cmd)

    # Run commands in specified XML
    if aXmlPath:
        _xml_path = aXmlPath
    else:
        _xml_path = aCluCtrl.mGetPatchConfig()
    _cmdout = _oedacli.mRun(_xml_path, _xml_path)
    ebLogTrace(_cmdout)
    ebLogInfo(f"XML {aCluCtrl.mGetPatchConfig()} has been modified to enable encryption")

def createEncryptionMarkerFileForVM(aDom0: str, aDomU: str):
    """
    Function to create a marker file in aDom0 that is used to tell
    that aDomU has fs encryption enabled
    """

    # aDomU will be the FQDN, and we know the hostname cannot have dots (.)
    try:
        _hostname = aDomU.split(".")[0]
        _marker_file = f"fs_encryption_keyapi_{_hostname}"
    except Exception as e:
        _err = (f"Something unexpected happend while creating the luks marker file. "
            f"Please review the error, fix and retry")
        ebLogError(_err)
        raise ExacloudRuntimeError(0x96, 0x0A, _err)

    _marker_file = os.path.join("/opt/exacloud/fs_encryption", _marker_file)

    with connect_to_host(aDom0, get_gcontext()) as _node:

        ebLogInfo(f"Creating encryption LUKS marker file: '{_marker_file}' for {aDomU}")

        # Make sure Directory exists before copying keyapi
        _bin_mkdir = node_cmd_abs_path_check(_node, "mkdir")
        _cmd = f"{_bin_mkdir} -p {os.path.dirname(_marker_file)}"
        node_exec_cmd_check(_node, _cmd)

        # touch it, timestamp is not used for anything
        _bin_touch = node_cmd_abs_path_check(_node, "touch", sbin=True)
        _cmd = f"{_bin_touch} {_marker_file} "
        node_exec_cmd_check(_node, _cmd)

        ebLogInfo(f"Created: '{_marker_file}' in '{aDom0}'")

def deleteEncryptionMarkerFileForVM(aDom0: str, aDomU: Optional[str]=None):
    """
    Function to delete the marker file from aDom0 that is used to tell
    that aDomU has fs encryption enabled. If no aDomU is passed, we delete the
    whole directory
    """

    if aDomU:
        # aDomU will be the FQDN, and we know the hostname cannot have dots (.)
        try:
            _hostname = aDomU.split(".")[0]
            _marker_file = f"fs_encryption_keyapi_{_hostname}"
        except Exception as e:
            _err = (f"Something unexpected happend while deleting the luks marker file. "
                f"Please review the error, fix and retry")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x96, 0x0A, _err)

        _file_to_rm = os.path.join("/opt/exacloud/fs_encryption", _marker_file)
    else:
        _file_to_rm = "/opt/exacloud/fs_encryption"

    with connect_to_host(aDom0, get_gcontext()) as _node:

        ebLogInfo(f"Deleting encryption LUKS marker file: '{_file_to_rm}'")

        # Delete the file, the -r doesn't affect if the file is regular or directory
        _bin_rm = node_cmd_abs_path_check(_node, "rm")
        _cmd = f"{_bin_rm} -rf {_file_to_rm} "
        node_exec_cmd_check(_node, _cmd)

        ebLogInfo(f"Deleted: '{_file_to_rm}' in '{aDom0}'")


def copyOedaExaCCKeyApiToNode(aHost: str, aDomU: str, aRemoteKeyapiPath: str):
    """
    Function to copy the keyapi from Exacloud to aHost under the path
    aRemoteKeyapiPath. This is the flow to be run for ExaCC
    """

    _local_keyapi_path = \
            "scripts/fs_encryption/fs_encryption_key_api_exacc.py"

    # Get patchserver IP from DomU -- eth0 -1
    with connect_to_host(aDomU, get_gcontext()) as _node:

        # Fetch commands binaries
        _ip_bin = node_cmd_abs_path_check(node=_node, cmd="ip", sbin=True)

        # Fetch eth0 ip address and netmask
        _eth0_ipaddr = node_exec_cmd_check(
            node = _node,
            cmd = f"{_ip_bin} -f inet addr show eth0 ")

        # Attempt creation of ip_interface, assume 1st position is
        # ip address
        try:
            _eth0_regex = re.search(r"inet.+",  _eth0_ipaddr.stdout)
            _eth0_interface = ip_interface(_eth0_regex.group().split()[1])

        except Exception as exp:
            _err_msg = (f"Unable to fetch ip address from: "
                        f"{_eth0_ipaddr.stdout} on eth0 "
                        f"on: {aDomU}, stderr: {_eth0_ipaddr.stderr}")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x97, 0xA, _err_msg) from exp

        # To verify we are not in ATP, we check that the ip address of eth0
        # is part of the link local block CIDR. If it's not part of it, then
        # we raise an error
        if not _eth0_interface.ip.is_link_local:
            _err_msg = (f"Ip address of eth0: '{_eth0_interface.ip}' is not "
                       "part of link local block. This is nop")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x97, 0xA, _err_msg)

        # Compute nat ip, which should be the IP of eth0 - 1
        _patchserver_ip = IPv4Address(_eth0_interface.ip) - 1

        # Compute eth0 link local network
        # The first host is always eth0 ip - 2, subnet is always /30 which
        # allows 4 IPs for each domU network (per dom0)
        _link_local_first_host = IPv4Address(_eth0_interface.ip) - 2
        # We scape the subnet to avoid issues with 'sed'
        _link_local_network = ip_network(f"{_link_local_first_host}/30")
        _link_local_network = f"{_link_local_first_host}\/30"

        if _patchserver_ip not in _eth0_interface.network.hosts():
            _err_msg = (f"Unable to calculate a valid ecra nat ip for: '{aDomU}'"
                       f" Ip address {_patchserver_ip} not part "
                       f"of network {_eth0_interface.network}")
            ebLogError(_err_msg)

        ebLogInfo(f"Calculated patchserver IP: {_patchserver_ip} for {aDomU}")


    with connect_to_host(aHost, get_gcontext()) as _node:

        ebLogInfo(f"Copying the exacc keyapi to node {aHost}")

        # Make sure Directory exists before copying keyapi
        _bin_mkdir = node_cmd_abs_path_check(_node, "mkdir")
        _directory = os.path.dirname(aRemoteKeyapiPath)
        _cmd = f"{_bin_mkdir} -p {_directory} "
        node_exec_cmd_check(_node, _cmd)

        # Copy contents of _local_keyapi_shell into _tmp_local_keyapi_shell
        _node.mCopyFile(_local_keyapi_path, aRemoteKeyapiPath)

        # Get CPS PORT number
        _patchserver_port = get_gcontext().mGetConfigOptions().get(
                "exacc_fsencryption_port", "2080")
        ebLogInfo(f"Exacloud detected CPSAgent port {_patchserver_port}")

        # Replace the CPS PORT on the file
        node_exec_cmd_check(_node,
            (f"/bin/sed -i 's/_CPS_PORT=None/_CPS_PORT={_patchserver_port}/' "
            f"{aRemoteKeyapiPath}"))

        # Grep file to have confirmation of replacement
        _out_grep = node_exec_cmd_check(_node,
                f"/bin/grep '_CPS_PORT' {aRemoteKeyapiPath}")
        ebLogTrace(_out_grep)

        # Replace CPS IP
        node_exec_cmd_check(_node,
            (f"""/bin/sed -i 's/_CPS_IP=None/_CPS_IP="{_patchserver_ip}"/' """
            f"{aRemoteKeyapiPath}"))

        # Grep file to have confirmation of replacement
        _out_grep = node_exec_cmd_check(_node,
                f"/bin/grep '_CPS_IP' {aRemoteKeyapiPath}")
        ebLogTrace(_out_grep)

        # Replace ETH0 IP address
        node_exec_cmd_check(_node,
            (f"""/bin/sed -i 's/_ETH0_IP=None/_ETH0_IP="{_eth0_interface.ip}"/' """
            f"{aRemoteKeyapiPath}"))

        # Grep file to have confirmation of replacement
        _out_grep = node_exec_cmd_check(_node,
                f"/bin/grep '_ETH0_IP' {aRemoteKeyapiPath}")
        ebLogTrace(_out_grep)

        # Replace ETH0_NETWORK
        node_exec_cmd_check(_node,
            (f"""/bin/sed -i 's/_ETH0_NETWORK=None/_ETH0_NETWORK="{_link_local_network}"/' """
            f"{aRemoteKeyapiPath}"))

        # Grep file to have confirmation of replacement
        _out_grep = node_exec_cmd_check(_node,
                f"/bin/grep '_ETH0_NETWORK' {aRemoteKeyapiPath}")
        ebLogTrace(_out_grep)



def copyOEDAKeyApiToNode(aHost: str, aRemoteKeyapiPath: str,
        aDomU: str, aOptions: dict, aIsExaCC: bool, aVersionNumber: int = None):
    """
    Function to copy the keyapi from Exacloud to aHost under the path
    aRemoteKeyapiPath

    :param aHost: string representing node where to copy the keyapi
    :param aRemoteKeyapiPath: string representing remote path where to copy the keyapi
    :param aDomU: a String representing the secret name to write in the
        config file that the keyapi will use, this name will be the domU FQDN
    :param aOptions: dictionary representing the aOptions object
    """

    # Use local dummy passphrase if dev/qa environment detected and required
    # property is present in exabox.conf
    if useLocalPassphrase():
        ebLogInfo("Using dummy keyapi instead as dev/qa env is detected")
        return copyLocalOEDAKeyApiToDom0(aHost, aRemoteKeyapiPath)

    if aIsExaCC:
        ebLogInfo("Using ExaCC Keyapi instead as ExaCC is detected")
        return copyOedaExaCCKeyApiToNode(aHost, aDomU, aRemoteKeyapiPath)

    # Declare variables
    _local_key_api_shell = "scripts/fs_encryption/fs_encryption_key_api_oeda.sh"
    _local_key_api_binary = "packages/keyapi"

    # The local keyapi will not have embedded the encoded Go binary by default
    # We must patch it here with the encoded keyapi and config values
    # needed to fetch the remote passphrase using the go binary

    # We can avoid the copy if aHost contains already the keyapi with the correct
    # values. While working on the PoC on how to verify if aHost has the correct values
    # already, I noticed the penalty for checking this and for making the copy all the
    # times was negligible, so I decided to always copy the keyapi
    # This penalty of less than 5 seconds will guarantee that if in a cluster we delete
    # a node and add it back again with a different DomU name (as almost always is the
    # case) we will not face issues of the new node using the old node passphrase
    # Even though we have logic to remove the keyapi during a delete node, we don't
    # fail in Exacloud in case that fails, so always copying this will help us avoid
    # issues due to a stale keyapi
    with connect_to_host(aHost, get_gcontext()) as _node:

        ebLogInfo(f"Copying the keyapi to node {aHost}")

        # Make sure Directory exists before copying keyapi
        _bin_mkdir = node_cmd_abs_path_check(_node, "mkdir")
        _directory = os.path.dirname(aRemoteKeyapiPath)
        _cmd = f"{_bin_mkdir} -p {_directory} "
        ebLogTrace(_cmd)
        node_exec_cmd_check(_node, _cmd)

        # Build dictionary to hold keyapi config file information
        _remote_resources = parseEncryptionPayload(aOptions, "domU")

        _remote_config = dict()
        _remote_config["vault_ocid"] = _remote_resources.vault_ocid
        _remote_config["hostname"] = aDomU

        if aVersionNumber:
            _remote_config["version_number"] = aVersionNumber
        
        _remote_config_json = json.dumps(_remote_config)
        ebLogInfo(f"Remote config: {_remote_config_json}")

        # Create copy of local keyapi shell script to patch with encoded
        # go binary and config file
        with tempfile.NamedTemporaryFile(delete=True, mode='a') as _tmp_local_keyapi_shell:

            # Copy local keyapi shell script to patch it
            shutil.copyfile(_local_key_api_shell, _tmp_local_keyapi_shell.name)
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the keyapi beggining marker and move position to the end
            _tmp_local_keyapi_shell.write("\n__KEYAPI_BEGINS__\n")
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the base64 encoded keyapi binary in the _tmp_local_keyapi_shell
            # Use base64.encodebytes instead of base64.base64encode to add the extra
            # \n every 76 bytes
            with open(_local_key_api_binary, mode="br") as _tmp_local_keyapi_bin:
                _tmp_local_keyapi_shell.write(base64.encodebytes(
                    _tmp_local_keyapi_bin.read()).decode("utf-8"))
                _tmp_local_keyapi_shell.seek(0,2)

            # Add the keyapi end marker
            _tmp_local_keyapi_shell.write("\n__KEYAPI_ENDS__\n")
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the keyapi beggining marker
            _tmp_local_keyapi_shell.write("\n__CONFIG_BEGINS__\n")
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the base64 encoded keyapi binary in the _tmp_local_keyapi_shell
            _tmp_local_keyapi_shell.write(base64.b64encode(
                _remote_config_json.encode("utf-8")).decode("utf-8"))
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the keyapi end marker
            _tmp_local_keyapi_shell.write("\n__CONFIG_ENDS__\n")
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the certs beggining marker and move position to the end
            # NOTE: it's possible that we write nothing between the BEGIN/END
            # markers of the CERTS. This will make the keyapi use the default
            # certs in the cavium, e.g. http://169.254.169.254/opc/v1/identity/
            _tmp_local_keyapi_shell.write("\n__CERTS_BEGINS__\n")
            _tmp_local_keyapi_shell.seek(0,2)

            # Add the proper certificates for R1 in the shell wrapper
            if mIsR1():

                _r1_cert = "exabox/kms/combined_r1.crt"
                # Add the base64 encoded certs file in the _tmp_local_keyapi_shell
                # Use base64.encodebytes instead of base64.base64encode to add the extra
                # \n every 76 bytes
                with open(_r1_cert, mode="br") as _tmp_local_cert:
                    _tmp_local_keyapi_shell.write(base64.encodebytes(
                        _tmp_local_cert.read()).decode("utf-8"))
                    _tmp_local_keyapi_shell.seek(0,2)

            # Add the certs end marker
            _tmp_local_keyapi_shell.write("\n__CERTS_ENDS__\n")
            _tmp_local_keyapi_shell.seek(0,2)

            # Since the tmp file will be deleted after close(), force a flush() before
            # copying it
            _tmp_local_keyapi_shell.flush()

            # Copy contents of _local_keyapi_shell into _tmp_local_keyapi_shell
            _node.mCopyFile(_tmp_local_keyapi_shell.name, aRemoteKeyapiPath)


def copyLocalOEDAKeyApiToDom0(aHost: str, aRemoteKeyapiPath: str):
    """
    Function to copy the keyapi from Exacloud to aHost under the path
    aRemoteKeyapiPath

    :param aHost: string representing node where to copy the keyapi
    :param aRemoteKeyapiPath: string representing remote path where to copy the keyapi
    """

    # Declare variables
    _local_key_api = "scripts/fs_encryption/fs_encryption_key_api_oeda_r1.sh"

    # Copy keyapi shell script to aHost with aRemoteKeyapiPath name
    with connect_to_host(aHost, get_gcontext()) as _node:

        if _node.mFileExists(aRemoteKeyapiPath):
            ebLogInfo(f"The keyapi is already present in Dom0 {aHost}")
        else:
            ebLogInfo(f"The keyapi is NOT present in Dom0 {aHost}, copying it...")

            # Make sure Directory exists before copying keyapi
            _bin_mkdir = node_cmd_abs_path_check(_node, "mkdir")
            _directory = os.path.dirname(aRemoteKeyapiPath)
            _cmd = f"{_bin_mkdir} -p {_directory} "
            ebLogTrace(_cmd)
            node_exec_cmd_check(_node, _cmd)

            # Copy it
            _node.mCopyFile(_local_key_api, aRemoteKeyapiPath)

            # Set ownership go binary
            _bin_chown = node_cmd_abs_path_check(_node, "chown")
            _cmd = f"{_bin_chown} root:root {aRemoteKeyapiPath}"
            ebLogTrace(_cmd)
            node_exec_cmd_check(_node, _cmd)

            # Set permissions go binary
            _bin_chmod = node_cmd_abs_path_check(_node, "chmod")
            _cmd = f"{_bin_chmod} 500 {aRemoteKeyapiPath}"
            ebLogTrace(_cmd)
            node_exec_cmd_check(_node, _cmd)


#
# u02 encrypted creation support
#

def createu02ZipFileFromDep(aDom0:str, aCluCtrl:any, aRemoteZipPath: str):
    """
    Method to create a zip file from the dep files from the aHost default location to
    the path specified in aImageName

    :param aDom0: string representing the Dom0 on where to create the zip file
    :param aCluCtrl: Clucontrol object
    :param aImageName: a String representing the name to assign to the image created
    :param aRemoteDynDir: a String representing the path in the Dom0 where to create
        the zip file
    """

    # Declare variables
    _packages_list = aCluCtrl.mDynDepImageList(['nid']) + \
             aCluCtrl.mDynDepNonImageList(['db_templates', 'bdcs', 'rpm', 'ocde_bits'])
    _dyndep_version, _ = aCluCtrl.mDyndepFilesList()
    _u02_zip = os.path.basename(aRemoteZipPath)
    _remote_dyn_dir = os.path.dirname(aRemoteZipPath)

    # Check the image is not already present in the Dom0, used for undo/retry of WF
    # Do nothing if already present and assume this is from an undo/retry
    # Use the field 'force_recreate_u02_encrypted' in exabox.conf to force recreation
    with connect_to_host(aDom0, get_gcontext()) as _node:
        if _node.mFileExists(aRemoteZipPath) and not \
            (get_gcontext().mGetConfigOptions().get(
                "force_recreate_u02_encrypted", "False")).upper() == "TRUE":
            ebLogInfo(f"The image file '{aRemoteZipPath}' is already present in "
                f"'{aDom0}', this is a no-op")
            return

        # Get commands binaries
        _bin_mkdir = node_cmd_abs_path_check(_node, "mkdir")
        _bin_chmod = node_cmd_abs_path_check(_node, "chmod")
        _bin_cp = node_cmd_abs_path_check(_node, "cp")
        _bin_mv = node_cmd_abs_path_check(_node, "mv")
        _bin_rm = node_cmd_abs_path_check(_node, "rm")
        _bin_zip = node_cmd_abs_path_check(_node, "zip")

        # Define a tmp directory to hold images and create zip file
        _tmp_dir = os.path.join(_remote_dyn_dir, aCluCtrl.mGetUUID())

        node_exec_cmd_check(_node, f"{_bin_mkdir} -p {_tmp_dir}")
        node_exec_cmd_check(_node, f"{_bin_mkdir} -p {_tmp_dir}/opt/dbaas_images/managed")
        node_exec_cmd_check(_node, f"{_bin_mkdir} -p {_tmp_dir}/opt/bdcs")
        node_exec_cmd_check(_node, f"{_bin_chmod} a+x {_tmp_dir}/opt")

        for _oss in _packages_list:

            _dom0file = _oss['dom0']

            if 'bdcs' in list(_oss.keys()) and _oss['bdcs'] == 'True':
                _dest_dir = '/opt/bdcs/'

            elif 'managed' in list(_oss.keys()) and _oss['managed'] == 'True':
                _dest_dir = '/opt/dbaas_images/managed/'

            else:
                _dest_dir = '/opt/dbaas_images/'

            _cmd = f"{_bin_cp} {_dom0file} {_tmp_dir}{_dest_dir}"
            ebLogTrace(f"{_cmd} on {_node.mGetHostname()}")
            node_exec_cmd_check(_node, _cmd)

        ebLogInfo(f"Attempting to create zip file: {_u02_zip} in {_tmp_dir}")

        # Zip command
        _cmd = f"cd {_tmp_dir} ; {_bin_zip} -r {_u02_zip} opt/"
        ebLogTrace(f"'{_cmd}' on {_node.mGetHostname()}")
        node_exec_cmd_check(_node, _cmd)

        # Move zip file to base_remote directory to be grabbed by OEDACLI later
        _cmd = f"{_bin_mv} {_tmp_dir}/{_u02_zip} {_remote_dyn_dir}"
        node_exec_cmd_check(_node, _cmd)
        ebLogTrace(_cmd)

        ebLogInfo(f"Zip file {_remote_dyn_dir}/{_u02_zip} created successfully "
                f"in {_node.mGetHostname()}")

        node_exec_cmd_check(_node, f"{_bin_rm} -rf {_tmp_dir}")
        ebLogInfo(f"Removing stage dir: {_bin_rm} -rf {_tmp_dir}")


def createu02ZipFileFromDepParallel(aHostList:str, aCluCtrl:any, aRemoteZipPath: str):
    """
    Helper function to execute in parallel the creation of the u02 zip file in
    aHostList

    :param aHostList: list of dom0 on where to create u02 file for u02 encrypted creation
    :param: aCluCtrl: exaBoxCluCtrl object
    :param aImageName: a String representing the name to assign to the image created
    :param aRemoteDynDir: a String representing the path in the Dom0 where to create
        the zip file

    :returns None:
    """

    # Create Process Manager
    _plist = ProcessManager()

    # Create one process per Host from aHostList and append the process to Process Manager
    for _host in aHostList:
        ebLogInfo("Spawning process to build zip file for u02 encrypted creation in "
            f"{_host}")

        _p = ProcessStructure(createu02ZipFileFromDep,
             (_host, aCluCtrl, aRemoteZipPath, ),)
        _p.mSetMaxExecutionTime(20*60) # 20 minutes timeout
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)

    _plist.mJoinProcess()
    ebLogInfo("Finished creating u02 zip file for /u02 encrypted creation: "
        f"{(_plist.mGetReturnKeyValues())}")

def createEncryptedLVM(aDom0: str, aDomU: str, ebox: any, aZipFile: str, aSize:int,
        aType: str, aKeyApi: str) -> None:
    """
    This function will attempt to create an encrypted LVM in a KVM Host

    :param aDom0: String representing the Dom0 where aDomU exists
    :param aDomU: String representing the DomU where to create the Encrypted image
    :param ebox: Clucontrol object
    :param aZipFile: String representing the path of the zip file to be used as source
    :param aSize: a string representing the size of the image to create
    :param aType: a string representing the type of filesystem we'll create
    :param aKeyApi: a String representing the keyapi to be used by oedacli, this can be
                    either a path for a keyapi in exacloud or a URL for oeda to fetch the
                    keyapi from a remote location
    """

    ebLogInfo(f"Attempting to create Encrypted image, using {aZipFile} for {aDomU}")

    # Declare variables to use
    _imagefile = os.path.basename(aZipFile)
    _filename = f"{os.path.splitext(_imagefile)[0]}.img"
    _image_path = os.path.join("/EXAVMIMAGES", "GuestImages", aDomU, _filename)

    # Check the image is not already present in the Dom0, used for undo/retry of WF
    # Do nothing if already present and assume this is from an undo/retry
    # Use the field 'force_recreate_u02_encrypted' in exabox.conf to force recreation
    with connect_to_host(aDom0, get_gcontext()) as _node:
        if _node.mFileExists(_image_path) and not \
            (get_gcontext().mGetConfigOptions().get(
                "force_recreate_u02_encrypted", "False")).upper() == "TRUE":
            ebLogInfo(f"The image file '{_image_path}' is already present in "
                f"'{aDom0}', this is a no-op")
            return

    _cmd = (f'ALTER MACHINE ACTION=CREATEIMAGE IMAGEFILE={_filename} FILESYSTEM={aType}'
            f' KEYAPI="{aKeyApi}" ZIPFILE={aZipFile} SIZE={aSize} '
            f'WHERE HOSTNAME={aDomU}')
    ebLogTrace(_cmd)

    # Create Instance of ebOedacli using oedacli with keys in WorkDir
    _oedacli_bin = os.path.join(ebox.mGetOedaPath(), "oedacli")
    _oedacli = ebOedacli(_oedacli_bin, os.path.join(ebox.mGetOedaPath(), "log"),
            aLogFile="oedacli_encrypt.log")
    _oedacli.mSetAutoSaveActions(True)
    _oedacli.mSetDeploy(True)
    _oedacli.mAppendCommand(_cmd)

    # Run commands to create imagefile
    _cmdout = _oedacli.mRun(ebox.mGetPatchConfig(), ebox.mGetPatchConfig())

    ebLogTrace(_cmdout)
    ebLogInfo(f"Succesfully created image {_imagefile} in host: '{aDomU}'")

def buildEncryptedVDisk(aCluCtrl:any, aKeyApiPath:str):
    """
    This function will attempt to build an encrypted disk to be mounted on /u02
    1- Get lock on Hosts
    2- Get size of u02
    3- Create zip file containing dep files, in Hosts (this is parallel op)
    4- Use oedacli to create the encrypted image in the Hosts

    :param: aCluCtrl: exaBoxCluCtrl object
    :param aImageName: a String representing the name to assign to the image created

    :returns: the path of where the Zip file was created with u02 contents, to be
        consummed by oedacli to attach the encrypted image
    """

    # Declare variables
    _disk_u02_name = "u02_extra_encrypted"
    _zip_u02_name = f"{_disk_u02_name}.zip"
    _dyndep_version, _ = aCluCtrl.mDyndepFilesList()
    _zip_remote_file_path = os.path.join("/EXAVMIMAGES", "GlobalCache", aCluCtrl.mGetKey(), _dyndep_version, _zip_u02_name)

    # Fetch vDisk size
    _disk_u02_size = aCluCtrl.mGetu02Size()
    ebLogInfo(f"*** Add vDisk (encrypted) u02 size {_disk_u02_size}")

    ebLogInfo(f"Attempting to create encrypted {_disk_u02_name} image")

    with aCluCtrl.remote_lock():

        # Create u02 zip file needed to create the encrypted u02 disk (this can be done
        # in parallel
        _dom0_list = [ _dom0 for _dom0 , _domu in aCluCtrl.mReturnDom0DomUPair()]
        createu02ZipFileFromDepParallel(_dom0_list, aCluCtrl, _zip_remote_file_path)

        # Use vm_maker to create encrypted image, parallel oedacli not support for now
        for _dom0, _domU in aCluCtrl.mReturnDom0DomUPair():
            createEncryptedLVMVmMaker(_dom0, _domU, aCluCtrl, _zip_remote_file_path,
                    _disk_u02_size, "ext4")

    return _zip_remote_file_path, f"{_disk_u02_name}.img"

def createEncryptedLVMVmMaker(aDom0: str, aDomU: str, ebox: any, aZipFile: str, aSize:int,
        aType: str) -> None:
    """
    This function will attempt to create an encrypted LVM in a KVM Host using
    vm_maker directly

    :param aDom0: String representing the Dom0 where aDomU exists
    :param aDomU: String representing the DomU where to create the Encrypted image
    :param ebox: Clucontrol object
    :param aZipFile: String representing the path of the zip file to be used as source
    :param aSize: a string representing the size of the image to create
    :param aType: a string representing the type of filesystem we'll create
    """

    ebLogInfo(f"Attempting to create Encrypted image, using {aZipFile} for {aDomU}")

    # Declare variables to use
    _imagefile = os.path.basename(aZipFile)
    _filename = f"{os.path.splitext(_imagefile)[0]}.img"
    _image_path = os.path.join("/EXAVMIMAGES", "GuestImages", aDomU, _filename)

    _allow_msdos_gdisk_conversion = get_gcontext().mGetConfigOptions().get(
            "fs_encryption_allow_msdos_gdisk_conversion", "false")

    _allow_creating_gpt_disk = get_gcontext().mGetConfigOptions().get(
            "fs_encryption_allow_gpt_disk_creation", "false")

    # Check the image is not already present in the Dom0, used for undo/retry of WF
    # Do nothing if already present and assume this is from an undo/retry
    # Use the field 'force_recreate_u02_encrypted' in exabox.conf to force recreation
    with connect_to_host(aDom0, get_gcontext()) as _node:

        if _node.mFileExists(_image_path):
            if not (get_gcontext().mGetConfigOptions().get(
                "force_recreate_u02_encrypted", "False")).upper() == "TRUE":
                ebLogInfo(f"The image file '{_image_path}' is already present in "
                    f"'{aDom0}', this is a no-op")
                return
            else:
                ebLogInfo(f"The image file '{_image_path}' is already present in "
                    f"'{aDom0}', deleting it to recreate")
                _bin_rm  = node_cmd_abs_path_check(_node, "rm")
                node_exec_cmd(_node, f"{_bin_rm} -rf {_image_path}")

        _bin_vm_maker = node_cmd_abs_path_check(_node, "vm_maker", sbin=True)
        _bin_grep = node_cmd_abs_path_check(_node, "grep")


        # Check if vm_maker supports MDSOS label type for creation
        _out_vm_maker_msdos_support = node_exec_cmd(
                _node, (f"{_bin_vm_maker} -h | {_bin_grep} -- "
                    f"'--create --disk-image ' | {_bin_grep} 'label' -i"))
        ebLogTrace(f"vm_maker output in {aDom0} is {_out_vm_maker_msdos_support}")

        # If grep find the argument, we use it to create the image MSDOS
        if _out_vm_maker_msdos_support.exit_code == 0:
            ebLogTrace(f"Detected MSDOS label support for image creation in "
                f"vm_maker for {aDom0}")
            _vm_maker_msdos_arg = "--label msdos"
            _label_already_msdos = True

        # If not, we check for exabox.conf 'fs_encryption_allow_msdos_gdisk_conversion'
        else:
            ebLogTrace(f"Detected MSDOS label support missing for image creation "
                f"in vm_maker for {aDom0}")
            _vm_maker_msdos_arg = ""
            _label_already_msdos = False

            if str(_allow_msdos_gdisk_conversion).lower() == "true":
                ebLogInfo(f"The exabox.conf flag "
                    "'fs_encryption_allow_msdos_gdisk_conversion' is enabled to "
                    f"allow the conversion of {_image_path} from GPT to MSDOS once "
                    "created")
            else:
                _err_msg = (f"The exabox.conf flag "
                    "'fs_encryption_allow_msdos_gdisk_conversion' is disabled to "
                    f"allow the conversion of {_image_path} from GPT to MSDOS once "
                    "created")
                _action_msg = (f"Please set the exabox.conf flag "
                    f"'fs_encryption_allow_msdos_gdisk_conversion' to 'True' and "
                    f"then undo/retry the step")
                ebLogCritical(_err_msg, _action_msg)
                raise ExacloudRuntimeError(0x96, 0x0A, _action_msg)

        # If label will be created as GPT, verify that GDISK is available
        _package_bits = []
        if not _label_already_msdos:
            _gdisk_local_rpm = "images/gdisk.x86_64.rpm"
            _package_bits = glob.glob(_gdisk_local_rpm)
            if not _package_bits:
                if str(_allow_creating_gpt_disk).lower() == "true":
                    ebLogWarn(f"The gdisk rpm is not found under "
                        f"{_gdisk_local_rpm} in the exacloud local filesystem. "
                        f"Exacloud cannot proceed. The exabox.conf flag "
                        "'fs_encryption_allow_gpt_disk_creation' is set to 'true' "
                        "so we will skip the GPT -> MSDOS conversion step. ")
                else:
                    _err_msg = (f"The gdisk rpm is not found under {_gdisk_local_rpm} "
                        "in the exacloud local filesystem. Exacloud cannot proceed "
                        f"with the creation of the encrypted image {_image_path} "
                        "as GPT, since we don't have a way to convert it to MSDOS ")
                    _action_msg = (f"Please stage the gdisk rpm in {_gdisk_local_rpm} "
                        f"local filesystem and undo/retry the step.")
                    ebLogCritical(_err_msg, _action_msg)
                    raise ExacloudRuntimeError(0x96, 0x0A, _action_msg)
            else:
                _package_bits = _package_bits.pop()
                ebLogInfo(f"Found the rpm {_package_bits}")

        # Use vm_maker to create the image
        _out_create_img = node_exec_cmd_check(
                _node, (f"{_bin_vm_maker} --create --disk-image {_image_path} "
                f"--size {aSize} --filesystem {aType} --from-zip {aZipFile} "
                f"{_vm_maker_msdos_arg} --encrypt"),
                log_error=True, log_stdout_on_error=True)

    # If label is GPT and 'fs_encryption_allow_msdos_gdisk_conversion' is True
    # we convert the partition type in here
    if not _label_already_msdos:
        if not _package_bits and str(_allow_creating_gpt_disk).lower() == "true":
            ebLogWarn(f"Skipping GPT->MSDOS conversion in {_image_path} since "
                "gdisk rpm is missing and exabox.conf flag "
                "'fs_encryption_allow_gpt_disk_creation' is 'true' ")
        else:
            ebLogInfo(f"Converting GPT-MSDOS the image {_image_path}")
            convertGptToMsdosLabelDriver(aDom0, _image_path)

    ebLogTrace(_out_create_img)
    ebLogInfo(f"Succesfully created image {_image_path} in host: '{aDomU}'")

def convertGptToMsdosLabelDriver(aDom0, aImageFile):
    """
    Main function to make sure the disk label type is MSDOS
    for the main partition in the image file aImageFile
    If not, we'll use 'gdisk' to convert it

    :param aDom0: dom0 where to manipulate the imagefile
    :param aImageFile: the image file whos partition we want
        to convert to msdos (we assume the image has 1 partition
        always)
    """

    with connect_to_host(aDom0, get_gcontext()) as _node:
        # Check current disk label
        _disk_label = getDiskLabel(_node, aImageFile)

        if _disk_label == MSDOS:
            ebLogInfo(f"Disk label in {aDom0} for {aImageFile} is already {_disk_label}")

        # if label is GPT, check if gdisk is installed in dom0
        elif _disk_label == GPT:
            ebLogInfo(f"Disk label in {aDom0} for {aImageFile} is gpt, will convert to msdos")

            # Install gdisk rpm
            installGdiskRpm(_node)

            # Convert disk label
            convertGptToMsdosLabel(_node, aImageFile)

            # uninstall gdisk rpm
            removeGdiskRpm(_node)

        else:
            _err_msg = (f"Disk label in {aDom0} for {aImageFile} is not msdos not gpt, "
                "recreate the disk by undoig/retrying the step")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

def getDiskLabel(aNode, aImageFile)-> str:
    """
    :param aNode: a node already connected to the host where we'll check the
        image disk label
    :param a aImageFile: the path to the image to get its disk label
    """
    _bin_partprobe = node_cmd_abs_path_check(aNode, "partprobe", sbin=True)

    _out_part = node_exec_cmd_check(aNode,
            f"{_bin_partprobe} {aImageFile} -ds")
    ebLogTrace(f"Partprobe output: {_out_part} in {aNode}")

    # For GPT we expect this output
    # /EXAVMIMAGES/GuestImages/<vm_name>/<image>: gpt partitions 1
    if "gpt part" in _out_part.stdout.strip():
        return GPT

    # For MSDOS we expect this output
    elif "msdos part" in _out_part.stdout.strip():
        return MSDOS

    else:
        ebLogWarn(f"Unkown partition disk label in {aNode.mGetHostname()} "
            f"for {aImageFile}")
        return _out_part.stdout.strip()


def installGdiskRpm(aNode):
    """
    :param aNode: a node already connected to the host where we'll check the
        image disk label
    """

    _local_rpm = "images/gdisk.x86_64.rpm"
    _remote_rpm = "/tmp/gdisk.x86_64.rpm"

    _bin_rpm = node_cmd_abs_path_check(aNode, "rpm", sbin=True)
    _out_rpm_query = node_exec_cmd(aNode, f"{_bin_rpm} -q gdisk")
    if  _out_rpm_query.exit_code == 0:
        ebLogInfo(f"RPM already installed: {_out_rpm_query.stdout.strip()}")
    else:
        aNode.mCopyFile(_local_rpm, _remote_rpm)
        ebLogInfo(f"Installing rpm {_remote_rpm} in {aNode.mGetHostname()}")
        _out_rpm_install = node_exec_cmd(aNode,
                f"{_bin_rpm} -ivh {_remote_rpm}")
        ebLogInfo(f"Installed rpm {_remote_rpm} in {aNode.mGetHostname()}, "
            f"output is: {_out_rpm_install}")


def removeGdiskRpm(aNode):
    """
    :param aNode: a node already connected to the host where we'll check the
        image disk label
    """

    _bin_rpm = node_cmd_abs_path_check(aNode, "rpm", sbin=True)
    _out_rpm_query = node_exec_cmd(aNode, f"{_bin_rpm} -q gdisk")
    ebLogTrace(f"rpm query in {aNode.mGetHostname()} is {_out_rpm_query}")
    if  _out_rpm_query.exit_code == 0:
        ebLogInfo(f"RPM installed: {_out_rpm_query.stdout.strip()}, "
            "will remove")
        _out_rpm_uninstall = node_exec_cmd(aNode,
                f"{_bin_rpm} -e --allmatches gdisk")
        ebLogInfo(f"RPM gidks removed in {aNode.mGetHostname()}: "
            f"{_out_rpm_uninstall}")
    else:
        ebLogInfo(f"RPM gdisk not found in {aNode.mGetHostname()}")

def convertGptToMsdosLabel(aNode, aImageFile):
    """
    :param aNode: a node already connected to the host where we'll convert the
        image disk label
    :param a aImageFile: the path to the image to convert its disk label
    """

    ebLogInfo(f"Running gdisk to convert GPT to MSDOS in {aImageFile}!")
    _bin_gdisk = node_cmd_abs_path_check(aNode, "gdisk", sbin=True)
    node_exec_cmd_check(
        aNode,
        f"/bin/echo -e 'r\ng\nw\nY\n' | {_bin_gdisk} {aImageFile}"
    )


def attachEncryptedVDiskToKVMGuest(aCluCtrl: any, aImageFile: str, aZipFile: str,
        aMountPoint: str, aKeyApi:str, aDom0DomUPairList:list=[])->None :
    """
    This function will attempt to attach an already created encrypted Disk to a KVM Guest
    using oedacli.
    :param aCluCtrl: Clucontrol object
    :param aImageFile: String representing the name of the ImageFile to attach
    :param aZipFile: String representing the path of the zip file to be used as source
    :param aMountPoint: String representing the mount point that is desired to be used
        to mount aImageFile
    :param aKeyApi: a String representing the keyapi to be used by oedacli, this can be
                    either a path for a keyapi in exacloud or a URL for oeda to fetch the
                    keyapi from a remote location
    :param aDom0DomUPairList: an Optional argument to specify the list of
        Dom0/DomUs where to attach the image
    """

    if aDom0DomUPairList:
        _ddpair = aDom0DomUPairList
    else:
        _ddpair = aCluCtrl.mReturnDom0DomUPair()

    for _dom0, _domU in _ddpair:

        # Check the image is not already attached  in the domU, useful for undo/retry of WF
        # Do nothing if already present and assume this is from an undo/retry
        with connect_to_host(_dom0, get_gcontext()) as _node:
            _bin_grep = node_cmd_abs_path_check(_node, "grep")
            _cmd = (f'/opt/exadata_ovm/vm_maker --list --disk-image --domain {_domU} | '
                f'{_bin_grep} "{aImageFile}"')
            ebLogTrace(_cmd)
            _out_list_disks = node_exec_cmd(_node, _cmd)
            if _out_list_disks.exit_code == 0:
                ebLogInfo(f"The disk '{aImageFile}' is already attached to "
                    f"'{_domU}', this is a no-op for this DomU")
                continue
            elif _out_list_disks.exit_code != 1:
                _err_msg = (f"Exacloud failed to check if {aImageFile} is already "
                    f"attached to {_domU}, {_out_list_disks}")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        # Create Instance of ebOedacli using oedacli with keys in WorkDir
        ebLogInfo(f"Attempting attach of {aImageFile} on {_domU}")
        _oedacli_bin = os.path.join(aCluCtrl.mGetOedaPath(), "oedacli")
        _oedacli = ebOedacli(_oedacli_bin, os.path.join(aCluCtrl.mGetOedaPath(), "log"),
                                aLogFile="oedacli_encrypt.log")
        _oedacli.mSetAutoSaveActions(True)
        _oedacli.mSetDeploy(True)

        # Declare attach command to use
        _cmd = (f'ALTER MACHINE ACTION=ATTACHDISK IMAGEFILE={aImageFile} '
                f'MOUNTPATH={aMountPoint} ZIPFILE={aZipFile} KEYAPI="{aKeyApi}" '
                f'GUESTACCESS=true WHERE HOSTNAME={_domU}')
        ebLogInfo(_cmd)
        _oedacli.mAppendCommand(_cmd)

        try:
            # KEYAPI argument should point to a script that fetches the keyfile
            # This keyapi, if passed as a path to OEDA, should be copied to the Node.
            # If passed as a URL there's no need to copy anything
            # but the keyapi should be available to OEDA in the URL specified for download
            copyOEDAKeyApiToNode(aHost = _domU,
                    aRemoteKeyapiPath = aKeyApi,
                    aDomU = _domU,
                    aOptions = aCluCtrl.mGetArgsOptions(),
                    aIsExaCC = aCluCtrl.mIsOciEXACC())

            # If we're in ExaCC, we set the socket in the dom0
            if aCluCtrl.mIsOciEXACC():
                mSetLuksPassphraseOnDom0Exacc(aCluCtrl, _dom0, _domU, aWait=False)

            # Run commands to attach imagefile
            _cmdout = _oedacli.mRun(aCluCtrl.mGetPatchConfig(), aCluCtrl.mGetPatchConfig())

        # Make sure to delete the keyapi from the domU regardless of success or error
        finally:
            _cmd = f"/bin/rm -rf {os.path.dirname(aKeyApi)}"
            ebLogTrace(_cmd)
            with connect_to_host(_domU, get_gcontext()) as _node:
                node_exec_cmd_check(_node, _cmd)
            ebLogInfo(f"The keyapi dir '{os.path.dirname(aKeyApi)}' has been deleted from {_domU}")


        ebLogInfo(_cmdout)
        ebLogInfo(f"Succesfully attached image {aImageFile} in host: '{_domU}'")

        # If the disk got attached successfully, then we set the proper ownership for it
        # assuming the mountpoint is /u02. Since we can technically use this logic to
        # attach any disk, I hard coded the below to happen to /u02 only
        if aMountPoint == "/u02":
            _ownership = "oracle.oinstall"
            _cmd = f"/bin/chown -fR {_ownership} {aMountPoint}"
            ebLogTrace(_cmd)
            with connect_to_host(_domU, get_gcontext()) as _node:
                node_exec_cmd_check(_node, _cmd)
            ebLogInfo(f"Ownership of '{aMountPoint}' set to {_ownership} on {_domU}")


def patchEncryptedKVMGuest(aCluCtrl: any, aOptions: dict, aDom0DomUPair=None) -> None:
    """
    This function handles creation and attaching of encripted u02 image

    :param: aCluCtrl: exaBoxCluCtrl object
    :aOptions dict: payload option dictionary

    Steps:
        1- Build Encrypted image in KVM Host, i.e. u02, image using oedacli
        2- Attach the image to the KVM Guests

    :raises ExacloudRuntimeError: if an error occurs while creating/attaching
        the u02 disk
    :returns None:
    """

    # Make Sure keyapi is present in the dom0s
    _clu_name = aCluCtrl.mGetClusters().mGetCluster().mGetCluName()
    _remote_keyapi_dir = os.path.join("/tmp", "fs_encryption")
    _keyapi_name = f"fs_encryption_keyapi_{_clu_name}"
    _remote_keyapi_path = os.path.join(_remote_keyapi_dir, _keyapi_name)

    if aDom0DomUPair:
        _ddp = aDom0DomUPair
    else:
        _ddp = aCluCtrl.mReturnElasticAllDom0DomUPair()

    # Create the clusterjson file for fs encryption in exacc
    if (aCluCtrl.mIsKVM() and aCluCtrl.mIsOciEXACC() and
            exacc_fsencryption_requested(aOptions)):
        aCluCtrl.mSaveClusterDomUList()

    # Copy the keyapi to each Dom0
    for _dom0, _domU in _ddp:

        # KEYAPI argument should point to a script that fetches the keyfile
        # We need to patch the XML with the keyapi path to be used to fetch the remote
        # passphrase from the VM. This keyapi, if passed as a path to OEDA should be
        # copied to the Host. If passed as a URL there's no need to copy anything
        # but the keyapi should be available to OEDA in the URL specified for download
        copyOEDAKeyApiToNode(aHost = _dom0,
                aRemoteKeyapiPath = _remote_keyapi_path,
                aDomU = _domU,
                aOptions = aCluCtrl.mGetArgsOptions(),
                aIsExaCC = aCluCtrl.mIsOciEXACC())

    _node_recovery = False
    if 'node_recovery_flow' in list(aOptions.jsonconf.keys()) and aOptions.jsonconf['node_recovery_flow'] == True:
        _node_recovery = True

    if aCluCtrl.mGetCmd() in ['vmbackup'] and aOptions and aOptions.vmbackup_operation in ["restore"] and _node_recovery:
        _disk_u02_name = "u02_extra_encrypted"
        _zip_u02_name = f"{_disk_u02_name}.zip"
        _dyndep_version, _ = aCluCtrl.mDyndepFilesList()
        _zip_image_path = os.path.join("/EXAVMIMAGES", "GlobalCache", aCluCtrl.mGetKey(), _dyndep_version, _zip_u02_name)
        _image_name = f"{_disk_u02_name}.img"

        # Attach encrypted image in KVM Guest
        # Inside of it do it no-op if already present, check all nodes
        attachEncryptedVDiskToKVMGuest(aCluCtrl, _image_name, _zip_image_path, "/u02", _remote_keyapi_path)
    else:
        # Create encrypted u02 image in Host
        # Inside of it do it no-op if already present, check all nodes
        _zip_image_path, _image_name = buildEncryptedVDisk(aCluCtrl, _remote_keyapi_path)

        # Attach encrypted image in KVM Guest
        # Inside of it do it no-op if already present, check all nodes
        attachEncryptedVDiskToKVMGuest(aCluCtrl,
                _image_name, _zip_image_path, "/u02",
                _remote_keyapi_path)


def addEncryptionProperties(aCluCtrl: any) -> None:
    """
    This function is to add some properties that OEDACLI needs in a property file
    that are currently missing.
    If the property already exists, this function won't attempt to add it

    :raises ExacloudRuntimeError: If an error occurs while checking if a property
        exists, or while attempting to add a missing property
    :returns None:
    """

    # Declare variables
    _property_file = os.path.join(aCluCtrl.mGetOedaPath(), "properties",
        "s_LinuxKvm.properties")

    # This dict has as keys the property names and as values their respective property value
    _properties_map = {
            "ENCRYPT_ATTACH_ENCRYPT": " --attach-encrypt {0} --key-api {1} --mountpoint {2} --filesystem-type {3}",
            "SETUPENCRYPTEXE": "/usr/sbin/setup_encrypt",
            }

    # Review and add, if missing, each property from the properties map
    for _property_name, _property_value in _properties_map.items():

        # Check if property doesn't already exist
        _cmd = f'/bin/grep "{_property_name}" {_property_file}'
        ebLogTrace(_cmd)
        _rc, _, _o, _ = aCluCtrl.mExecuteLocal(_cmd)

        # Do nothing if already present
        if _rc == 0:
            ebLogTrace(f"The property '{_property_name}' is already present in '{_property_file}'")
            return

        # Add it if missing
        elif _rc == 1:
            ebLogInfo(f"The property '{_property_name}' is not present in '{_property_file}'")
            _cmd = f"/bin/sed -i '$ a\{_property_name}={_property_value}' {_property_file}"
            ebLogTrace(_cmd)
            aCluCtrl.mExecuteLocal(_cmd)

        else:
            _err_msg = f"Something weird happened while checking the file '{_property_file}'"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

def useLocalPassphrase() -> bool:
    """
    This function will check if the specific config value is set
    in exabox.conf to enable using a local passphrase for luks
    devices

    :returns:
        True if we detec we should  use local passphrase in
            this environment
        False otherwise
    """

    # Check environment type and local passphrase property
    _env_type = get_gcontext().mGetConfigOptions().get("env_type", "prod")
    _local_passphrase = get_gcontext().mGetConfigOptions().get(
            "local_fs_passphrase", "False")

    if _env_type.upper() == "DEV" and _local_passphrase.upper() == "TRUE":
        ebLogInfo("Detected environment to use local luks passphrase")
        return True

    else:
        ebLogTrace("Using remote luks passphrase")
        return False


def deleteOEDAKeyApiFromDom0(ebox: any, aDom0List: list) -> None:
    """
    This function will delete the  keyapi shell wrapper from the Dom0s
    NOTE: The deletion of the remote passphrase kept in Secrets in Vault
        service is done already in 'deleteRemotePassphraseSiV'

    :param ebox: a Clucontrol object
    :param aDom0List: List of Dom0s where to delete the keyapi
    :raises ExacloudRuntimeError: if an error happens while removing the shell
        wrapper
    :returns None:
    """

    # The KeyAPI is expected to be present in this path in the Dom0's
    # The file name has the clustername as suffix
    _clu_name = ebox.mGetClusters().mGetCluster().mGetCluName()
    _remote_keyapi_dir = "/opt/exacloud/fs_encryption"
    _keyapi_name = f"fs_encryption_keyapi_{_clu_name}"
    _remote_keyapi_path = os.path.join(_remote_keyapi_dir, _keyapi_name)

    # Delete it
    for _dom0 in aDom0List:

        with connect_to_host(_dom0, get_gcontext()) as _node:

            _bin_rm = node_cmd_abs_path_check(_node, "rm")
            _cmd = f"{_bin_rm} -f {_remote_keyapi_path}"
            ebLogTrace(_cmd)
            node_exec_cmd_check(_node, _cmd)
            ebLogInfo(f"Deleted the keyapi '{_remote_keyapi_path}' for encrypted "
                    f"filesystems in: '{_dom0}'")

def validateMinImgEncryptionSupport(aEbox, aDom0DomUPair):
    """
    Validates if all the nodes from aDom0DomUPair are using an exadata image
    above the minimum required to support Encryption at rest

    :returns bool:
        True if all the nodes are using an image above the minimum
            required.
        False: If at least one node doesn't meet the image requirements
    """

    # Encryption is supported starting from 23.1.9
    # If any node uses an image version below that,
    # we must raise an error
    _ignore_cutoff_ver = get_gcontext().mGetConfigOptions().get(
        "ignore_fsencryption_cutoff", "false")

    # Get cutoff from exabox.conf
    # Bug 36624871: we need a vm_maker fix
    # present after (TBD) 23.1.20 or 24.1.2
    _fs_cutoff_ver_24_dom0 = get_gcontext().mGetConfigOptions().get(
        "fs_encryption_cutoff_ver_24.1_dom0")
    _fs_cutoff_ver_23_dom0 = get_gcontext().mGetConfigOptions().get(
        "fs_encryption_cutoff_ver_23.1_dom0")

    _fs_cutoff_ver_24_domU = get_gcontext().mGetConfigOptions().get(
        "fs_encryption_cutoff_ver_24.1_domU")
    _fs_cutoff_ver_23_domU = get_gcontext().mGetConfigOptions().get(
        "fs_encryption_cutoff_ver_23.1_domU")

    ebLogInfo("FS Encryption minimum image version required for dom0s is "
        f"{_fs_cutoff_ver_24_dom0} for images greater than 24.1 or "
        f"{_fs_cutoff_ver_23_dom0} for images lower than 24.1.")

    ebLogInfo("FS Encryption minimum image version required for domUs is "
        f"{_fs_cutoff_ver_24_domU} for images greater than 24.1 or "
        f"{_fs_cutoff_ver_23_domU} for images lower than 24.1.")
    
    if None in [_fs_cutoff_ver_23_domU, _fs_cutoff_ver_23_dom0,
        _fs_cutoff_ver_24_domU, _fs_cutoff_ver_24_dom0]:
        _err_msg = (f"Invalid exadata image versions for FS Encryption detected. "
            f"Make sure the $EC_HOME/exabox.conf '_fs_cutoff_ver_*' fields "
            "are present, or disable encryption on the input payload "
            "and undo/retry")
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    _nodes_img_check_fail = []

    for _dom0, _domU in aDom0DomUPair:

        _dom0_ver = aEbox.mGetExadataImageFromMap(_dom0)

        # Dom0 checks
        if (version_compare(_dom0_ver, "24.1") >= 0 and
            version_compare(_dom0_ver, _fs_cutoff_ver_24_dom0) >=0 ):
            ebLogInfo(f"Node {_dom0} meets FS Encryption image "
                f"version requirements: {_dom0_ver}")
        elif (version_compare(_dom0_ver, "24.1") < 0 and
            version_compare(_dom0_ver, _fs_cutoff_ver_23_dom0) >=0):
            ebLogInfo(f"Node {_dom0} meets FS Encryption image "
                f"version requirements: {_dom0_ver}")
        else:
            ebLogInfo(f"Dom0 {_dom0} doesn't meet FS Encryption "
                "image version requirements: {_dom0_ver}")
            _nodes_img_check_fail.append(_dom0)

        # DomU checks
        _domU_ver = aEbox.mGetExadataImageFromMap(_domU)
        if (version_compare(_domU_ver, "24.1") >= 0 and
            version_compare(_domU_ver, _fs_cutoff_ver_24_domU) >= 0):
            ebLogInfo(f"DomU {_domU} meets FS Encryption image "
                "version requirements, {_domU_ver}")
        elif (version_compare(_domU_ver, "24.1") < 0 and
            version_compare(_domU_ver, _fs_cutoff_ver_23_domU) >= 0):
            ebLogInfo(f"DomU {_domU} meets FS Encryption image "
                "version requirements, {_domU_ver}")
        else:
            ebLogInfo(f"DomU {_domU} doesn't meet FS Encryption "
                "image version requirements")
            _nodes_img_check_fail.append(_domU)

    if _nodes_img_check_fail:
        if _ignore_cutoff_ver.lower() == "true":
            ebLogWarn("Ignoring cutoff version as requested by "
                "exabox.conf flag 'ignore_fsencryption_cutoff'")
            return True

        else:
            _err_msg = (f"Nodes [{_nodes_img_check_fail}] failed the "
                f"minimum image version requirements for Encryption . "
                "Disable encryption on the input payload or upgrade "
                "the nodes and undo/retry")
            ebLogError(_err_msg)
            return False

    ebLogInfo(f"All nodes passed the fs encryption image requirement")
    return True

def cleanupU02EncryptedDisk(aDom0DomUPair):
    """
    This function will connect to each Dom0/Host and will try
    to detach the u02 disk from the corresponding DomU
    It will also try to cleanup the DomU fstab and reboot it
    as I saw many instances where IOCTL errors happened when
    trying to retach the same device (*RESCAN or similar alternatives
    can be considered later)

    :aDom0DomUPair: a tuple of dom0/domU pairs

    """

    for _dom0, _domU in aDom0DomUPair:

        # Try to unmounte /u02 on the domUs (if at all present)
        with connect_to_host(_domU, get_gcontext()) as _node:


            ebLogInfo(f"{_domU} -- Attempting to unmount /u02 "
                f"(no-op if not mounted)")
            _out_unmount = node_exec_cmd(_node, f"/bin/unmount /u02")
            ebLogTrace(_out_unmount)

            # Close luks volume (if present)
            _luks_volume = "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt"
            ebLogInfo(f"{_domU} -- Attempting to close {_luks_volume} "
                f"(no-op if not mounted)")
            _bin_cryptsetup = node_cmd_abs_path_check(
                    _node, "cryptsetup", sbin=True)
            _out_close = node_exec_cmd(
                    _node, f"{_bin_cryptsetup} close {_luks_volume}")
            ebLogTrace(_out_close)

            # Remove u02 from fstab (if at all present)
            ebLogInfo(f"{_domU} -- Attempting to remove fstab /u02 "
                f"entry (no-op if not present)")
            _out_fstab = node_exec_cmd(
                    _node, 'cat /etc/fstab | grep -v /u02 > /etc/fstab.orig; cp /etc/fstab.orig /etc/fstab')
            ebLogTrace(_out_fstab)

        # Now try to remove the disk u02 using vm_maker from the dom0 (if at all present)
        with connect_to_host(_dom0, get_gcontext()) as _node:

            _extra_disk = f"/EXAVMIMAGES/GuestImages/{_domU}/u02_extra_encrypted.img"

            # Remove u02 disk
            if _node.mFileExists(_extra_disk):
                ebLogInfo(f"{_dom0} -- Attempting to detach {_extra_disk} disk image (no-op if not present)")
                _out_detach = node_exec_cmd(_node, f"vm_maker --detach --disk-image {_extra_disk} --domain {_domU}")
                ebLogTrace(_out_detach)

                ebLogInfo(f"{_dom0} -- Attempting to remove {_extra_disk} disk image (no-op if not present)")
                _out_rm = node_exec_cmd(_node, f"/bin/rm -f {_extra_disk}")
                ebLogTrace(_out_rm)

            # Restart the domU, this is the best way to avoid hitting
            # IOCTL issues when trying to rettach the u02 disk.
            # We should be able to spend time to review the specific step
            # missing to  achieve a full cleanup. For now a reboot is the best
            # reliable/fast way (only affects undo of exacc with fs
            # encryption)
            shutdown_domu(_node, _domU)
            time.sleep(5)
            start_domu(_node, _domU)

def setupU01EncryptedDiskParallel(aEbox, aOptions, aDom0DomUPair, aMountPoint="/u01"):
    """
    Entry point to encrypt /u01 on the DomUs
    Doc: https://confluence.oraclecorp.com/confluence/display/EDCS/EXACS+OL8+
    FS+Encryption+Phase+2#EXACSOL8FSEncryptionPhase2-/u01Encryptionsupport

    This function will execute the u01 encryption steps in parallel in the
    nodes from aDom0DomUPair

    """

    # Create Process Manager
    _plist = ProcessManager()

    # Create one process per Dom0/DomU pair from aDom0DomUPair and append
    # the process to Process Manager
    for _dom0, _domU in aDom0DomUPair:

        ebLogInfo("Spawning process to execute u01 encryption steps in "
            f"{_dom0} - {_domU}")

        _p = ProcessStructure(setupU01EncryptedDiskPerHost,
             (aEbox, aOptions, _dom0, _domU, aMountPoint),)
        _p.mSetMaxExecutionTime(30*60) # 30 minutes timeout
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)

    _plist.mJoinProcess()

    # Check for timeouts
    if _plist.mGetStatus() == "killed":
        _err = "A timeout while checking encrypted first boot image existed"
        ebLogError(_err)
        ebLogTrace(_plist)
        raise ExacloudRuntimeError(0x0403, 0xA, _err)

    ebLogInfo("Finished the u01 encryption flow steps")

def setupU01EncryptedDiskPerHost(aEbox, aOptions, aDom0, aDomU,
        aMountPoint="/u01") -> int:
    """
    Entry point to encrypt /u01 on the DomUs
    Doc: https://confluence.oraclecorp.com/confluence/display/EDCS/EXACS+OL8+
    FS+Encryption+Phase+2#EXACSOL8FSEncryptionPhase2-/u01Encryptionsupport

    returns:
        0: Disk encrypted with success
        2: Disk already encrypted, doing nothing
    raises:
        ExacloudRuntimeError: if any major problem happens
    """

    # Get grid location
    _grid_loc , _, _ = aEbox.mGetOracleBaseDirectories(aDomU)
    if not _grid_loc:
        _grid_loc = aEbox.mGetClusters().mGetCluster().mGetCluHome()

    # Get FS size
    _img_size_GB = aOptions.jsonconf.get("filesystems", {}).get(
            "mountpoints", {}).get(aMountPoint, None)
    if _img_size_GB:
        _img_size_GB = _img_size_GB[:-1]
        ebLogInfo(f"Detected size of {_img_size_GB} G")

    # In ExaCC we should use the default min size from OEDA in case the u01
    # size is not present
    elif aEbox.mIsOciEXACC():
        # Get OEDA min disk size property
        _img_size_OEDA_prop = aEbox.mGetOedaProperty("MINGUESTDISKSIZE")
        if not _img_size_OEDA_prop:
            _err_msg = (f"Could not parse default image size from OEDA "
                "properties")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

        ebLogWarn(f"Using OEDA default min disk size {_img_size_OEDA_prop} G")
        _img_size_GB = _img_size_OEDA_prop

    # In ExaCS we should always use the payload info, if u01 size
    # is missing we fail
    else:
        _err_msg = f"Could not parse image size from payload"
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    # Perform DomU steps
    with connect_to_host(aDomU, get_gcontext()) as _node:

        # Check if u01 is already mounted and encrypted
        # If True: we skip this step
        # If not encrypted or not present we can proceed
        _bin_findmnt = node_cmd_abs_path_check(_node, "findmnt")

        # Get block device, FS type, and FS label
        _cmd = f"{_bin_findmnt} -rno source,fstype,label {aMountPoint}"
        _out_findmnt = node_exec_cmd(_node, _cmd)
        #_block_device, _fs_type, *_fs_label = _out_findmnt.stdout.strip().split()

        if _out_findmnt.exit_code == 0:
            ebLogInfo(f"Mountpoint {aMountPoint} is found in {aDomU}")
            _is_already_luks = getMountPointInfo(_node, aMountPoint).is_luks
        else:
            ebLogWarn(f"Mountpoint {aMountPoint} not found in {aDomU}")
            _is_already_luks = False

        if _is_already_luks:
            ebLogInfo(f"The disk mounted in {aMountPoint} is detected to "
                "be already encrypted. We will skip the steps for {aDomU}")
            return 2
        else:
            ebLogInfo(f"Encryption is not detected in the disk meant to be "
                f"present in {aMountPoint}. We will proceed with "
                f"the steps to encrypt the disk in {aDomU}")


        # Stop any process/service using /u01 and any submountpoint and unmount
        # recursively
        # We wait here to make sure CRS is brought up before we check for it
        waitForSystemBoot(_node)
        _bin_lsof = node_cmd_abs_path_check(_node, "lsof", True)
        _bin_kill = node_cmd_abs_path_check(_node, "kill")
        if (_node.mFileExists(f"{_grid_loc}/bin/crsctl") and
                aEbox.mCheckCrsUp(aDomU)):
            ebLogInfo((f"CRS is up on {aMountPoint} in {aDomU}. "
                        "Attempting to stop it."))
            _crs_started = True
            _bin_crsctl = f"{_grid_loc}/bin/crsctl"

            _cmd = f"{_bin_crsctl} stop crs -f"
            _out_crs_stop = node_exec_cmd(_node, _cmd)
            ebLogTrace(_out_crs_stop)

        _cmd = f"{_bin_lsof} -- {aMountPoint}"
        _out_lsof = node_exec_cmd(_node, _cmd)
        ebLogTrace(_out_lsof)

        _cmd = f"{_bin_kill} -9 $({_bin_lsof} +t -- {aMountPoint})"
        _out_proc_sigkill = node_exec_cmd(_node, _cmd)
        ebLogTrace(_out_proc_sigkill)

        ebLogInfo(f"All processes relying on {aMountPoint} should be "
            "stopped now")
        _cmd = f"{_bin_lsof} -- {aMountPoint}"
        _out_lsof = node_exec_cmd(_node, _cmd)
        ebLogTrace(_out_lsof)

        # Log file
        _bin_cat = node_cmd_abs_path_check(_node, "cat")
        _file_fstab = "/etc/fstab"
        _out_cat = node_exec_cmd_check(_node, f"{_bin_cat} {_file_fstab}")
        ebLogTrace(f"Contents of {_file_fstab} from {aDomU} is:\n "
            f"{_out_cat.stdout}")

    # Perform Dom0 steps
    with connect_to_host(aDom0, get_gcontext()) as _node:

        _bin_vm_maker = node_cmd_abs_path_check(_node, "vm_maker", sbin=True)

        # Make sure there are no stale u01 encrypted images present nor
        # attached
        _disk_u01_name = "u01_encrypted"
        _u01_encrypted_img = os.path.join("/EXAVMIMAGES", "GuestImages",
                aDomU, f"{_disk_u01_name}.img")
        if _node.mFileExists(_u01_encrypted_img):
            ebLogWarn(f"Exacloud detected stale image {_u01_encrypted_img} in "
                f"{aDom0}, will delete it")
            node_exec_cmd_check(_node, f"/bin/rm -f {_u01_encrypted_img}")

        # Create a zip file to use as source to create the encrypted disk
        _zip_u01_name = f"{_disk_u01_name}.zip"
        _zip_u01_marker = f"{_disk_u01_name}.marker"
        _dyndep_version, _ = aEbox.mDyndepFilesList()
        _zip_source_file = os.path.join("/EXAVMIMAGES", "GlobalCache",
                aEbox.mGetKey(), _dyndep_version, _zip_u01_marker)

        _zip_remote_file_path = os.path.join("/EXAVMIMAGES", "GlobalCache",
                aEbox.mGetKey(), _dyndep_version, _zip_u01_name)

        _bin_zip = node_cmd_abs_path_check(_node, "zip", sbin=True)
        _bin_touch = node_cmd_abs_path_check(_node, "touch", sbin=True)
        _bin_mkdir = node_cmd_abs_path_check(_node, "mkdir", sbin=True)

        _zip_remote_dir = os.path.dirname(_zip_remote_file_path)

        node_exec_cmd_check(_node, f"{_bin_mkdir} -p {_zip_remote_dir}")
        node_exec_cmd_check(_node, f"{_bin_touch} {_zip_source_file}")
        node_exec_cmd_check(_node,
                f"{_bin_zip} {_zip_remote_file_path} {_zip_source_file}")

        # Copy the keyapi
        _clu_id = aEbox.mGetClusters().mGetCluster().mGetCluId()
        _clu_name = aEbox.mGetClusters().mGetCluster().mGetCluName()
        _remote_keyapi_dir = "/opt/exacloud/fs_encryption"
        _keyapi_name = f"fs_encryption_keyapi_{_clu_name}"
        _remote_keyapi_path = os.path.join(_remote_keyapi_dir, _keyapi_name)
        copyOEDAKeyApiToNode(aHost = aDom0,
                aRemoteKeyapiPath = _remote_keyapi_path,
                aDomU = aDomU,
                aOptions = aEbox.mGetArgsOptions(),
                aIsExaCC = aEbox.mIsOciEXACC())

        # Create a new encrypted image in the dom0 with vm_maker
        _fs_type = "xfs"
        createEncryptedLVM(aDom0, aDomU, aEbox, _zip_remote_file_path,
                _img_size_GB, _fs_type, _remote_keyapi_path)

        # Attach the new image image to the domU
        # Inside of it do it no-op if already present, check all nodes
        attachEncryptedVDiskToKVMGuest(aEbox, f"{_disk_u01_name}.img",
                _zip_remote_file_path, "/u01", _remote_keyapi_path,
                [(aDom0, aDomU)])

        # List disks attached to the domU
        _out_list_disks = node_exec_cmd_check(
            _node, f"{_bin_vm_maker} --list --disk --domain {aDomU}")
        # We expect this format:
        # [root@sea201602exdd001 ~]# vm_maker --list --disk --domain atpd-exa-dfuwg1.client.exaclouddev.oraclevcn.com
        # File /EXAVMIMAGES/GuestImages/atpd-exa-dfuwg1.client.exaclouddev.oraclevcn.com/System.img
        # File /EXAVMIMAGES/GuestImages/atpd-exa-dfuwg1.client.exaclouddev.oraclevcn.com/grid19.0.0.0.230718.img
        # File /EXAVMIMAGES/GuestImages/atpd-exa-dfuwg1.client.exaclouddev.oraclevcn.com/u01.img
        # File /EXAVMIMAGES/GuestImages/atpd-exa-dfuwg1.client.exaclouddev.oraclevcn.com/u02_extra_encrypted.img
        # [root@sea201602exdd001 ~]#

        _image_name = "u01.img"
        _images_to_detach = []
        for _image_entry in _out_list_disks.stdout.strip().splitlines():

            _image_path = _image_entry.split("File ")[1].strip()

            if _image_name in os.path.basename(_image_path):
                ebLogInfo(f"Detected image to delete {_image_path} in {aDom0}")
                _images_to_detach.append(_image_path)

                if _node.mFileExists(_image_path):
                    ebLogInfo(f"Detected image {_image_path} in {aDom0}")

                else:
                    ebLogWarn(f"Image {_image_path} from {_image_entry} not detected "
                        f"properly in {aDom0}, 'touching' it")
                    _bin_touch = node_cmd_abs_path_check(_node, "touch")
                    node_exec_cmd_check(_node, f"{_bin_touch} {_image_path}")


        # Delete the original non-encrypted image from the dom0
        if _images_to_detach:
            _bin_rm = node_cmd_abs_path_check(_node, "rm")
            for _image_to_detach in _images_to_detach:
                node_exec_cmd_check(_node, f"{_bin_vm_maker} --detach "
                    f"--disk-image {_image_to_detach} --domain {aDomU}")
                ebLogInfo(f"Detached {_image_to_detach} from {aDom0}")

                node_exec_cmd_check(_node, f"{_bin_rm} -f {_image_to_detach}")
                ebLogInfo(f"Deleted {_image_to_detach} from {aDom0}")
        else:
            ebLogWarn(f"No image to delete in {aDom0} for {aDomU}")

    # Run final steps in domU
    with connect_to_host(aDomU, get_gcontext()) as _node:

        # Log file
        _bin_cat = node_cmd_abs_path_check(_node, "cat")
        _file_fstab = "/etc/fstab"
        _out_cat = node_exec_cmd_check(_node, f"{_bin_cat} {_file_fstab}")
        ebLogTrace(f"Contents of {_file_fstab} from {aDomU} is:\n "
            f"{_out_cat.stdout}")

        # Make sure the u01 FS is marked as XFS (OEDA might mark it
        # as ext4)
        _out_sed = node_exec_cmd(_node,
                f"/bin/sed -i -E 's/(u01\\s+)ext4/\\1xfs/' {_file_fstab}")
        ebLogTrace(_out_sed)

        # Log file again
        _bin_cat = node_cmd_abs_path_check(_node, "cat")
        _file_fstab = "/etc/fstab"
        _out_cat = node_exec_cmd_check(_node, f"{_bin_cat} {_file_fstab}")
        ebLogTrace(f"Contents of {_file_fstab} from {aDomU} is:\n "
            f"{_out_cat.stdout}")

    # Success
    ebLogInfo(f"Encryption setup of {aMountPoint} in {aDomU} finished ok")
    return 0

def mSetLuksPassphraseOnDom0Exacc(aEbox, aDom0, aDomU, aWait=False, aWaitSeconds=300):
    """
    Sets the ExaCC FS Encryption socket with the passphrase
    to open u02 from inside the DomU

    :returns: An optional coment with information about
        the operation
    """

    if not (aEbox.mIsOciEXACC() and aEbox.mIsKVM() and luksCharchannelExistsInDom0(aDom0, aDomU)):
        _msg = "Encryption not detected, this flow is only to be run in ExaCC KVM Encrypted DomUs"
        ebLogTrace(_msg)
        return _msg

    try:
        _remote_pass_file = f"/opt/exacloud/fs_encryption/passphrases/fs_enc_{aDomU}"

        with connect_to_host(aDom0, get_gcontext()) as _node:
            _script_local = 'scripts/fs_encryption/create_socket.py'
            _script_remote = "/opt/exacloud/bin/create_socket.py"

            # Create directories
            _cmd_mkdir  = '/bin/mkdir -p {0}'
            _node.mExecuteCmdLog(_cmd_mkdir.format(os.path.dirname(_script_remote)))
            _node.mExecuteCmdLog(_cmd_mkdir.format(os.path.dirname(_remote_pass_file)))
            _node.mExecuteCmdLog(f"/bin/touch {_remote_pass_file}")

            # Copy script
            _node.mCopyFile(_script_local, _script_remote)
            _bin_nohup = node_cmd_abs_path_check(_node, "nohup", sbin=True)

            _passphrase = exacc_get_fsencryption_passphrase(aDomU)
            _passphrase = encapsulatePass(_passphrase)

            # Create remote passphrase file
            _node.mWriteFile(_remote_pass_file, _passphrase.encode())

            # Set up socket
            _cmd = (f'{_bin_nohup} /bin/sh -c "'
                f'/usr/bin/python3 {_script_remote} '
                f'-vm {aDomU} -file {_remote_pass_file} '
                f'-wait {aWaitSeconds} " & # pass NOLOG')

            # node_exec_cmd_check
            if aWait:
                _out_set = node_exec_cmd_check(_node, _cmd)
                ebLogTrace(f"DomU {aDomU} socket set output: {_out_set}")
            else:
                _node.mExecuteCmd(_cmd)
                ebLogTrace("Socket set and sent to background, proceeding")


    except Exception as e:
        _err = (f"An error happened while setting up the socket "
                f"for {aDomU} in {aDom0}. Error:\n {e}")
        ebLogError(_err)
        return str(e)

    finally:

        # Clean up passphrase file always
        with connect_to_host(aDom0, get_gcontext()) as _node:
            if _node.mFileExists(_remote_pass_file):
                # From man pages shred is not guaranteed to
                # be effective in jounaled fs such as ext4,xfs which
                # is the case for the dom0s. Still it has same
                # effect and cost of 'rm' so we're using it
                _bin_shred = node_cmd_abs_path_check(_node, "shred", sbin=True)
                node_exec_cmd(_node, f"{_bin_shred} -u {_remote_pass_file}",
                        log_stdout_on_error=True, log_error=True)

    return ""

def encapsulatePass(aPassphrase):
    """
    Encapsulates aPassphrase in the agreed format
    This format consiste on the passphrase being in a
    json object, where the KEY is 'content'
    The object is meant to be encoded in base64

    :returns: a string representing the encapsulated
        passphrase
    """

    return base64.b64encode(
            json.dumps(
                {"content": aPassphrase}
            ).encode()).decode()

def mRollbackDomUPassphraseRotation(aParams, aCurrentSecret):
    # Take objects from params
    _clients = aParams.get('clients')
    _secret = aParams.get('secret')

    # Deprecate newly created version and make previous version current version
    ebLogInfo("Removing CURRENT state from new secret version.")
    _vault_client = _clients.vault_client
    _composite_client = VaultsClientCompositeOperations(_vault_client)

    _update_secret_details = UpdateSecretDetails(
        current_version_number=aCurrentSecret.version_number
    )

    _composite_client.update_secret_and_wait_for_state(
        _secret.id,
        _update_secret_details,
        wait_for_states=["ACTIVE"]
    )
    
    ebLogInfo("Rolled back secret versions. Previous version is still set to CURRENT.")

def mRotateDomUPassphrase(aCluCtrl, aParams):
    """
    Rotates a domU's SiV remote passphrase. It is expected that the domU does
    in fact contain one and ONLY one passphrase. 

    :param aParams: Dictionary containing OCI Vault clients, Secret object,
    domU hostname and remote configuration.
    :returns: Response dictionary. Associated to the rotation operation's status.
    """
    # Create new empty response
    _response = {
        "hostname": aParams.get('hostname'),
        "success": "True",
        "comment": ""
    }

    # Create new secret version with new passphrase.
    # Doing this first ensures that new secret version is set to CURRENT and 
    # the previous one is set to PREVIOUS.
    _clients = aParams.get('clients')
    _secret = aParams.get('secret')
    try:
        createNewSecretVersion(
            _clients,
            aParams.get('resources'),
            _secret.id
        )
    except ExacloudRuntimeError as e:
        ebLogError(f"Could not create new secret version. ({str(e)})")
        _response["success"] = "False"
        _response["comment"] = str(e)
        return _response

    # Retrieve current password (PREVIOUS) and new password (CURRENT)
    _secrets_client = _clients.secrets_client

    _current_secret = _secrets_client.get_secret_bundle(
        _secret.id,
        stage="PREVIOUS"
    ).data

    _new_secret = _secrets_client.get_secret_bundle(
        _secret.id,
        stage="CURRENT"
    ).data

    # Check if domU has root access by attempting a connection as root user
    _domU = aParams.get('hostname')
    try:
        # If we get root access, copy new keyapi and execute setup_encrypt
        ebLogInfo(f"Checking connection to host {_domU} as root")

        with connect_to_host(_domU, get_gcontext(), username='root') as _node:
            ebLogInfo(f"Able to log in to {_domU} as root")

    except Exception as e:
        # If no root access, notify SRE about further steps
        _err_msg = f"Could not connect to {_domU}: {str(e)}. If customer does not have root " + \
        "access, then customer needs to get new keyapi handed over, then run \'<keyapi_command>\' " + \
        "to trigger the operation manually. Once passphrase is rotated, old secret deletion " + \
        "must be scheduled by SRE."
        ebLogError(_err_msg)
        _response["success"] = "False"
        _response["comment"] = _err_msg
        mRollbackDomUPassphraseRotation(aParams, _current_secret)
        return _response

    # Copy previous passphrase's keyapi shell wrapper to node
    _clu_name = aCluCtrl.mGetClusters().mGetCluster().mGetCluName()
    _local_keyapi_path = "scripts/fs_encryption/fs_encryption_key_api_oeda.sh"

    _remote_keyapi_dir = "/opt/exacloud/fs_encryption"
    _old_keyapi_name = f"fs_encryption_keyapi_old_{_clu_name}"
    _old_keyapi_path = os.path.join(_remote_keyapi_dir, _old_keyapi_name)

    ebLogInfo("Copying old keyapi shell file to node.")

    copyOEDAKeyApiToNode(
        _domU,
        _old_keyapi_path,
        _domU,
        aCluCtrl.mGetArgsOptions(),
        aCluCtrl.mIsOciEXACC(),
        aVersionNumber=_current_secret.version_number
    )

    # Make keyapi shell wrapper with new passphrase
    _new_keyapi_name = f"fs_encryption_keyapi_new_{_clu_name}"
    _new_keyapi_path = os.path.join(_remote_keyapi_dir, _new_keyapi_name)

    ebLogInfo("Creating new keyapi shell file for node.")

    copyOEDAKeyApiToNode(
        _domU,
        _new_keyapi_path,
        _domU,
        aCluCtrl.mGetArgsOptions(),
        aCluCtrl.mIsOciEXACC(),
        aVersionNumber=_new_secret.version_number
    )

    # Execute setup_encrypt (5 retries maximum)

    _max_retries = 5
    _retry_count = 0

    while _retry_count < _max_retries:
        try:
            with connect_to_host(_domU, get_gcontext(), username='opc') as _node:
                # Perform rotation
                ebLogInfo("Switching keys using setup_encrypt")
                _encrypt_cmd = "/usr/sbin/setup_encrypt --change-key LVDBDisk " + \
                "--vg-name VGExaDbDisk.u02_extra_encrypted.img " + \
                f"--fetch-old-key {_old_keyapi_path} " + \
                f"--fetch-new-key {_new_keyapi_path}"
                node_exec_cmd_check(_node, _encrypt_cmd, log_stdout_on_error=True)

                # Delete old shell wrapper
                _bin_rm = node_cmd_abs_path_check(_node, "rm")
                _cmd = f"{_bin_rm} -rf {_old_keyapi_path}"
                node_exec_cmd_check(_node, _cmd)
                break
        
        except Exception as e:
            # Log current attempts
            _retry_count += 1
            ebLogError(f"Attempt {_retry_count} failed with error: {e}.")
            
            # Log error and return failure response after exhausting all retries
            if _retry_count >= _max_retries:
                _err_msg = f"Could not change keyapi binary to point to new secret version " + \
                f"due to the following error: {e}"
                ebLogError(_err_msg)
                _response["success"] = "False"
                _response["comment"] = _err_msg
                mRollbackDomUPassphraseRotation(aParams, _current_secret)
                return _response
            
            # Wait 5 seconds to retry
            time.sleep(5)

    return _response
    

def mSetLuksChannelOnDom0Exacc(aEbox, aDom0, aDomU):
    """
    This function will make sure a socket/channel is created
    in the aDom0 for aDomU. This is expected to be run in KVM only.

    We expect to add a snippet like this to the domU xml
        <channel type='unix'>
            <target type='virtio' name='luks'/>
            <address type='virtio-serial' controller='0' bus='0' port='3'/>
        </channel>

    We use virt-xml to create this channel, using a cmd:
    $ virt-xml 7 --add-device --channel type=unix,target.type=virtio,
          target.name=luks,address.type=virtio-serial,
          address.controller=0,address.bus=0,address.port=1

    - To enable this channel, we must recreate the VM with
      a shutdown/start after modifying the XML
    """

    _channel_name = "vmfsexacc"
    ebLogInfo(f"Setting up socket channel for {aDomU} in {aDom0}")
    _options = aEbox.mGetArgsOptions()

    # Check if charchannel already exists in aDom0 for aDomU
    if not luksCharchannelExistsInDom0(aDom0, aDomU, _channel_name):

        with connect_to_host(aDom0, get_gcontext()) as _node:

            # Add it to the XML
            node_exec_cmd_check(_node, f"virt-xml {aDomU} --add-device --channel "
                "type=unix,target.type=virtio,"
                f"target.name={_channel_name},address.type=virtio-serial,"
                "address.controller=0,address.bus=0,address.port=2")

            shutdown_domu(_node, aDomU)

            time.sleep(5)
            start_domu(_node, aDomU)

        ebLogInfo(f"Socket channel set for {aDomU} in {aDom0}")

    else:
        ebLogInfo(f"Socket channel already set for {aDomU} in {aDom0}")


def luksCharchannelExistsInDom0(aDom0, aDomU, aChannelName="vmfsexacc"):
    """
    Makes sure that a unix type channel aChannelName is set
    on aDom0 for aDomU.
    We are looking for a file with this
    naming convention:
    "/var/lib/libvirt/qemu/channel/target/domain-11-gold-luks-real-k0obn/vmfsexacc"

    :returns bool:
        True: If aChannelName is already set for aDomU in aDom0
        False: If is not set
    """


    with connect_to_host(aDom0, get_gcontext()) as _node:

        _out_id = node_exec_cmd_check(_node, f"/usr/bin/virsh domid {aDomU}")
        _id = _out_id.stdout.strip()
        ebLogTrace(f"Domain ID for {aDomU} is {_id}")

        # Search using domain id
        _out_socket = node_exec_cmd(_node,
                f"/bin/ls /var/lib/libvirt/qemu/channel/target/domain-{_id}*/{aChannelName}")
        ebLogTrace(_out_socket)

        if _out_socket.exit_code == 0:
            ebLogInfo(f"Socket file {_out_socket.stdout} exists")
            return True
        else:
            ebLogTrace(f"Socket {aChannelName} doesn't exists for {aDomU}.\n{_out_socket}")
            return False


def dom0InjectPassphrase(aEbox):
    """
    Function to run the flow to set up the socket file
    for a given dom0/domU pair
    https://confluence.oraclecorp.com/confluence/display/EDCS/
    ExaCC+FedRamp+FS+Encryption+-+Exacloud+APIs
    """

    _input_vm_hostname = aEbox.mGetArgsOptions().vmid
    ebLogTrace(f"Parse DomU name {_input_vm_hostname} from payload")

    # Create generic response
    _response = {
        "vmid": _input_vm_hostname,
        "success": "False",
        "comment": "VM not found in input XML"
    }

    for _dom0, _domU in aEbox.mReturnDom0DomUPair():

        if _domU.split(".")[0] != _input_vm_hostname:
            ebLogInfo(f"Ignoring from XML pair {_dom0} - {_domU}")
            continue

        _resp = mSetLuksPassphraseOnDom0Exacc(aEbox, _dom0, _domU, aWait=True)
        if _resp == "":
            _suc_status = "True"
        else:
            _suc_status = "False"

        _response = {
                "vmid": _domU,
                "success": _suc_status,
                "comment": _resp
                }
        break

    return _response

def getDom0DomUPair(aEbox):
    _input_vm_hostname = aEbox.mGetArgsOptions().vmid
    ebLogTrace(f"Parse DomU name {_input_vm_hostname} from payload")

    for _dom0, _domU in aEbox.mReturnDom0DomUPair():

        if _domU.split(".")[0] == _input_vm_hostname:
            return _dom0, _domU

    return None, None

def domUsRotatePassphrase(aEbox):
    """
    Driver of the passphrase rotation operation for domUs.
    https://confluence.oraclecorp.com/confluence/display/EDCS/
    Encryption+Key+and+passphrase+rotation
    """

    # Get hostnames from payload
    _options = aEbox.mGetArgsOptions()
    _json = _options.jsonconf
    ebLogInfo(f"Options are: {_options}")
    ebLogInfo(f"JSON is: {_json}")
    _hostnames = _json.get("domus", [])
    ebLogTrace(f"Parsed list of DomU names {_hostnames} from payload")

    # Create generic response
    _response = {
        "domUs": [],
        "success": "True"
    }

    # Get information from payload about the OCI resources to be used to rotate
    # the passphrase
    _remote_oci_resources = parseEncryptionPayload(_options, "domu")

    # Initialize the required OCI Clients
    _oci_clients = createOCIClientsSetup(aRemoteOciResourcesTuple=_remote_oci_resources)
    _vault_client = _oci_clients.vault_client

    # Get all the SecretSummaries from current vault
    _remote_secrets = _vault_client.list_secrets(
        _remote_oci_resources.secret_compartment_ocid, 
        vault_id=_remote_oci_resources.vault_ocid
    ).data

    # For each domU, perform the rotation
    for _dom0, _domU in aEbox.mReturnDom0DomUPair():
        # Make sure to rotate only on the specified domUs
        if _domU.split(".")[0] not in _hostnames:
            ebLogInfo(f"Ignoring from XML pair {_dom0} - {_domU}")
            continue

        # Create domU operation tracker
        _domU_response = {
            "hostname": _domU,
            "success": "True",
            "comment": ""
        }

        # Get SecretSummary objects that match the domU's name
        _secret_name_pattern = re.compile(_domU)
        _filtered_secrets = [_sec for _sec in _remote_secrets if _secret_name_pattern.search(_sec.secret_name)]

        # Initialize rotation only if ONE passphrase is present
        if len(_filtered_secrets) != 1:
            _err_msg = f"Invalid amount of passphrases in {_domU}: ({len(_filtered_secrets)}). \
            Please delete any invalid secrets and check which is the current passphrase, then try again."
            _response["success"] = "False"
            _domU_response["success"] = "False"
            _domU_response["comment"] = _err_msg
            _response.get("domUs").append(_domU_response)
            continue

        # Track operation state to set an operation report for the current domU
        _secret = _filtered_secrets[0]
        _params = {
            "clients": _oci_clients,
            "secret": _secret, 
            "hostname": _domU, 
            "resources": _remote_oci_resources
        }

        # Attempt rotation
        try:
            _domU_response = mRotateDomUPassphrase(aEbox, _params)
            _response.get("domUs").append(_domU_response)
        except Exception as e:
            # Set responses
            _response["success"] = "False"
            _domU_response["success"] = "False"
            _domU_response["comment"] = f"Rotation failed due to error: {str(e)}"
            _response.get("domUs").append(_domU_response)
            # Log error and break loop
            ebLogError(f"Error during passphrase rotation for domU {_domU}. Please check for errors in response.")
            return _response

    return _response

def executeLuksOperation(aEbox):
    """
    Main driver for LUKS related operations.
    """

    _resp = {}
    _luks_operation = aEbox.mGetArgsOptions().luks_operation
    ebLogInfo(f"Luks Operations driver: {_luks_operation}")

    if _luks_operation == "dom0_inject_passphrase":
        #Fetching history console logs before injecting passphrase
        _dom0, _domU = getDom0DomUPair(aEbox)
        _log_file_1 = f"history_console-{aEbox.mGetUUID()}-{_domU}.log.1"
        fetchConsoleLogs(aEbox, _dom0, _domU, _log_file_1)

        _resp = dom0InjectPassphrase(aEbox)

         #Fetching history console logs after injecting passphrase
        _log_file_2 = f"history_console-{aEbox.mGetUUID()}-{_domU}.log.2"
        fetchConsoleLogs(aEbox, _dom0, _domU, _log_file_2)

        _vm_rebooted = checkForReboots(aEbox, _dom0, _domU, _log_file_1, _log_file_2)
        raiseAlarm(aEbox, _dom0, _domU, _vm_rebooted)
    elif _luks_operation == "passphrase_rotation":
        _resp = domUsRotatePassphrase(aEbox)
    else:
        ebLogError(f"Operation not supported")

    return _resp

def fetchConsoleLogs(aEbox, aDom0, aDomU, aFileName):
    _ebox = aEbox
    _dom0 = aDom0
    _domU = aDomU
    _remote_path = f"/tmp/{aFileName}"
    _localfile = f"{_ebox.mGetOedaPath()}/log/{aFileName}"

    with connect_to_host(_dom0, get_gcontext()) as _node:
        _cmd_str = f"/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host {_domU}  --path {_remote_path}"
        _node.mExecuteCmdLog(_cmd_str)
        if _node.mGetCmdExitStatus() != 0:
            ebLogError(f"fetchConsoleLogs: Failed to retreive history console log from dom0 {_dom0}")
            return False

        if _node.mFileExists(_remote_path):
            _node.mCopy2Local(_remote_path, _localfile)
            _node.mExecuteCmd(f"/bin/rm -rf {_remote_path}")
            if not os.path.exists(_localfile):
                ebLogError(f"Unable to copy file {_localfile}")
                return False
    ebLogTrace(f"Retreived console log in path: {_localfile}")
    return True

def checkForReboots(aEbox, aDom0, aDomU, aFile1, aFile2):
    _ebox = aEbox
    _dom0 = aDom0
    _domU = aDomU
    _log_file_1 = aFile1
    _log_file_2 = aFile2

    _reboot_string = _ebox.mCheckConfigOption('vm_reboot_consolelog_markers')
    with open(_log_file_1, "r") as _f1, open(_log_file_2, "r") as _f2:
        _diff = difflib.unified_diff(_f1.readlines(), _f2.readlines(), fromfile=_log_file_1, tofile=_log_file_2)
        for _line in _diff:
            if any(_s in _line for _s in _reboot_string):
                ebLogError(f"VM {_domU} was rebooted immediately after passphrase is injected.")
                deleteHistoryConsoleLogs(_ebox)
                return True
    deleteHistoryConsoleLogs(_ebox)
    return False

def deleteHistoryConsoleLogs(aEbox):
    _ebox = aEbox
    #remove files after comparision!
    _file_list = glob.glob(f"{_ebox.mGetOedaPath()}/log/history_console-{_ebox.mGetUUID()}-*")
    for _file in _file_list:
        os.remove(_file)

def createCSVFile(aDom0, aDomU, aVMState):
    _dom0 = aDom0
    _domU = aDomU
    _vm_state = aVMState
    _filename = "/tmp/vm_metrics.csv"

    _dom0_host = _dom0.split(".")[0]
    _domU_host = _domU.split(".")[0]
    with open(_filename, 'w') as _csvfile:
        _writer_obj = csv.writer(_csvfile, delimiter=',')
        if _vm_state:
            _writer_obj.writerow([f"{_dom0_host}", "domUFSEncryptionError", 0, f"vm={_domU_host}"])
        else:
            _writer_obj.writerow([f"{_dom0_host}", "domUFSEncryptionError", 1, f"vm={_domU_host}"])
    return _filename

def raiseAlarm(aEbox, aDom0, aDomU, aVMState):
    _ebox = aEbox
    _dom0 = aDom0
    _domU = aDomU
    _vm_state = aVMState

    _filename = createCSVFile(_dom0, _domU, _vm_state)
    _ebox.mExecuteLocal(f"/u01/exaT2/script/exacc_exacloud_send_event.sh {_filename}")
    _ebox.mExecuteLocal(f"/bin/rm -rf {_filename}")

class RSAEncryption(object):
    def __init__(self):
        self.__pub_key =  None
        self.__priv_key =  None

    def mLoadPublicKey(self, aPublicKey):
        _pub_key = aPublicKey.encode("utf-8")
        self.__pub_key = load_ssh_public_key(_pub_key)

    def mLoadPrivateKey(self, aPrivateKey, aPassword=None):
        _priv_key = aPrivateKey.encode("utf-8")
        _passwd = aPassword
        self.__priv_key = load_ssh_private_key(_priv_key, _passwd)

    def mEncryptKey(self, aKey):
        _key = aKey.encode("utf-8")
        _encrypted_key = self.__pub_key.encrypt(_key,
                                        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                        algorithm=hashes.SHA256(), label=None))
        return _encrypted_key

    def mDecryptKey(self, aEncryptedKey):
        _encrypted_key = aEncryptedKey
        _original_key = self.__priv_key.decrypt(_encrypted_key,
                                               padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                               algorithm=hashes.SHA256(), label=None))
        return _original_key.decode("utf-8")

class SymmetricEncryption(object):
    def __init__(self):
        self.__key = None
        self.mGenerateRandomKey()

    def mGenerateRandomKey(self):
        self.__len = 8
        self.__key = ''.join(random.choices(string.ascii_lowercase + string.digits, k = self.__len))

    def mGetKey(self):
        return self.__key

    def mSetKey(self, aKey):
        self.__key = aKey

    def mEncrypt(self, aData):
        _data = aData.decode("utf-8")
        _encrypted_data = mask(_data, self.__key, "utf-8")
        return _encrypted_data

    def mDecrypt(self, aEncData):
        _encrypted_data = aEncData
        _orig_data = umask(_encrypted_data, self.__key)
        return _orig_data.encode("utf-8")

def exacc_fsencryption_requested(aOptions:dict) -> bool:

    _options = aOptions
    if _options is None or _options.jsonconf is None:
        return False

    _json = _options.jsonconf
    if "fs_encryption" in list(_json.keys()):
        return True

    return False

def exacc_save_fsencryption_passphrase(aOptions:dict, aDomUList:list = list()) -> bool:

    _options = aOptions
    _domu_list = aDomUList

    if _options is None or _options.jsonconf is None:
        _err_msg = f"options information is invalid or empty."
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    _fsencryption_passphrase = None
    if useLocalPassphrase():
        try:
            _local_node = exaBoxNode(get_gcontext(), aLocal=True)
            _local_node.mConnect()
            _localpassphrase_file = f"/tmp/fs_encryptionpassphrase_{uuid.uuid1()}"
            _passphrase_file = createLocalFSKey(_local_node, _localpassphrase_file)
            with open(_passphrase_file, 'r') as _fd:
                _fsencryption_passphrase = _fd.read()
        except Exception as excep:
            _err_msg = f"options information is invalid or empty."
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)
        finally:
            if _local_node:
                _local_node.mDisconnect()
    else:
        _json = _options.jsonconf
        _fsencryption_passphrase = _json.get("fs_encryption", "")
        if len(_fsencryption_passphrase) == 0:
            _err_msg = f"Encryption passphrase received from payload is empty. Please check."
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    _save_successful = True
    for _domu in _domu_list:
        _exakms = ExaKmsKVDB()
        _exakms_entry = _exakms.mBuildExaKmsEntry(f"fs_encpass_{_domu}", _fsencryption_passphrase)
        _is_successful = _exakms.mInsertExaKmsEntry(_exakms_entry)
        if _is_successful:
            ebLogTrace(f"Persisted file system encryption passphrase for {_domu} in exakv.db")
        else:
            _save_successful = False
            ebLogError(f"Error while perisiting file system encryption passphrase for {_domu}")

    return _save_successful

def exacc_get_fsencryption_passphrase(aDomU:str) -> str:

    _domu = aDomU
    _plaintext_fsencryption_passphrase = None
    if _domu is None:
        _err_msg = f"domu information is empty."
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    _exakms = ExaKmsKVDB()
    _exakms_entry = _exakms.mSearchEntry(f"fs_encpass_{_domu}")

    if _exakms_entry:
        _plaintext_fsencryption_passphrase = _exakms_entry.mCreateValueFromEncData()

    return _plaintext_fsencryption_passphrase

def exacc_del_fsencryption_passphrase(aDomU:str) -> bool:

    _domu = aDomU
    if _domu is None:
        _err_msg = f"domu information is empty."
        ebLogError(_err_msg)
        raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

    _exakms = ExaKmsKVDB()
    _is_successful = _exakms.mDeleteExaKmsEntry(f"fs_encpass_{_domu}")
    return _is_successful

