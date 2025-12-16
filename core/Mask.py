"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Mask - mask/umask functions

FUNCTION:
    Ofuscation of sensitive information on exacloud

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    aypaul      04/29/25 - Bug#37535214 Check if input string is Salted or not.
    ririgoye    02/04/25 - Bug 37391243 - ECSREQ list function not working when
                           dealing with empty entries
    dekuckre    09/13/23 - 35774564: Fix umaskSensitiveData
    naps        04/05/23 - Bug 35259960 - Avoid unnessary checks during
                           masking, since it invokes mkstore which is
                           expensive.
    alsepulv    05/25/22 - Enh 33533440: Get default mask from wallet
    ndesanto    03/07/22 - Issue with old umask for ilom operations
    ndesanto    12/21/21 - Security requested the change of cipher
    ndesanto    02/28/20 - 30872387 - Remove PyCrypto usage
    ndesanto    01/15/20 - Python 3 migration changes
    sergutie    11/29/16 - Create file
"""

import six
import base64
import random
import pickle
import copy
import os
import shlex
import subprocess as sp

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.kms.crypt import isBase64, getKeyAndIV
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebThreadLocalLog, ebLogAgent
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

DLIMIT = 33
ULIMIT = 126
ASIZE = ULIMIT + 1 - DLIMIT
# The security bug 33360834 especifically metions to remove the hard coded
# mask, however becasue of compatibility we need to keep this variable, this
# should be removed in a future release with the rest of the fall back to ECB
# cipher functionality.
# TODO Remove DEFAULT_MASK, PADDING & BLOCK_SIZE constants when ECB code is
# removed.
PADDING = '.'
BLOCK_SIZE = 16
# MASK_SIZE must at least 8 for the mask and unmask functions logic to work preoperly.
MASK_SIZE = 8
MASK_SIZE_ECB = 32
SENSITIVE_FIELDS = ['oeda_pwd', 'default_pwd', 'ssh_passphrase', 'sshkey', 'ssh_private_key', 'root_spwd', 'db_connstr', 'adminpassword']
# AAD stand for Additional Associated Data
# This refers to data that is not encrypted but added to the encryption result,
# we don't currently use this field on GCM encryption, thus the constant with 
# value None
AAD = None


class MaskException(Exception):
    pass

def mExecuteLocal(aCmd, aCurrDir=None, aStdIn=sp.PIPE, aStdOut=sp.PIPE, aStdErr=sp.PIPE):

    _args = aCmd
    if isinstance(aCmd, str):
        _args = shlex.split(aCmd)

    _current_dir = aCurrDir
    _stdin = aStdIn
    _stdout = aStdOut
    _stderr = aStdErr

    _proc = sp.Popen(_args, stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=_current_dir)
    _stdoutP, _stderrP = _proc.communicate()
    _rc = _proc.returncode

    if _stdoutP:
        _stdoutP = _stdoutP.decode("UTF-8").strip()
    else:
        _stdoutP = ""

    if _stderrP:
        _stderrP = _stderrP.decode("UTF-8").strip()
    else:
        _stderrP = ""

    return _rc, _stdoutP, _stderrP


# TODO Remove idempotent and fix Unit Test case to reflect that
def mask(aString: str, aMask: Optional[Union[str, bytes]]=None, aMode: str=None) -> str:
    """
    Mask the provided string, encrypt the provided text to hide important
    information. 

    This function is idempotent. Mask/Encryption is applied only once, if 
    the text provided is already masked then the function performs no 
    operation and returns the provided text as provided.

    The algorithm used is AES GCM, this algorithm requires a key and iv,
    these are calculated using the mask, then added to the encrypted bytes
    and then b64encoded, resulting in at least 17 bytes being returned, the 
    format is "Salted__" + MASK_SIZE bytes of mask + encrypted message.

    Modes such as Authenticated Encryption with Associated Data (AEAD) 
    provide authenticity assurances for both confidential data and Additional 
    Associated Data (AAD) that is not encrypted. (Please see RFC 5116 for more 
    information on AEAD and AEAD algorithms such as GCM/CCM.) Both 
    confidential and AAD data can be used when calculating the authentication 
    tag (similar to a Mac). This tag is appended to the ciphertext during 
    encryption, and is verified on decryption.

    AEAD modes such as GCM/CCM perform all AAD authenticity calculations 
    before starting the ciphertext authenticity calculations. To avoid 
    implementations having to internally buffer ciphertext, all AAD data must 
    be supplied to GCM/CCM implementations (via the updateAAD methods) before 
    the ciphertext is processed (via the update and doFinal methods).

    Note that GCM mode has a uniqueness requirement on IVs used in encryption 
    with a given key. When IVs are repeated for GCM encryption, such usages 
    are subject to forgery attacks. Thus, after each encryption operation 
    using GCM mode, callers should re-initialize the cipher objects with GCM 
    parameters which has a different IV value.

    Arguments
        aString:str
            A str that can be ascii encoded to bytes.
        aMask(optional):str=None
            A str, bytes or None. Must be MASK_SIZE bytes long.
            None  - is the default and results in a randomly generated mask.
            str   - a str that can be ascii encoded to bytes
            bytes - a byte array
    """
    if not aString:
        return aString

    _mode: str = aMode
    _mask: Optional[Union[str, bytes]] = aMask
    if _mask is None:
        _mask = os.urandom(MASK_SIZE)
    elif isinstance(_mask, str):
        _mask = _mask.encode("ascii", "ignore")  # ignore
    elif not isinstance(_mask, bytes):
        raise ValueError("The mask function supports str, bytes or None on the mask argument.")

    # aMask validation must at least be MASK_SIZE bytes long
    if aMask and not len(aMask) >= MASK_SIZE:
        raise ValueError(f"aMask must be at least {MASK_SIZE} bytes long.")

    # At this point _mask is of type bytes and is populated
    key, iv = getKeyAndIV(_mask.decode("ascii", "ignore"), _mask)
    cipher: AESGCM = AESGCM(key)
    try:
        # Here we attempt to decrypt aString, this is done to prevent double
        #encryption of aString ( But not applicable for exacloud. See below comment )
        # But, in exacloud, oeda_pwd, default_pwd and root_spwd are only single encrption strings.
        # So, we dont really require below code. But, having it around, in case there is a future need!
        _decoded: bytes = base64.b64decode(aString)
        # The "Salted__" text is only present on the GCM encryption
        if _decoded[:MASK_SIZE] == b"Salted__":
            return aString
    except Exception:
        # aString is not masked, so continue and mask the content
        pass

    if _mode:
        ciphertext: bytes = cipher.encrypt(iv, aString.encode(_mode), AAD)
    else:
        ciphertext: bytes = cipher.encrypt(iv, aString.encode("ascii"), AAD)
    openssl_ciphertext: bytes = b"Salted__" + _mask + ciphertext
    return six.ensure_text(base64.b64encode(openssl_ciphertext))

def checkifsaltedandb64encoded(aString: str) -> bool:

    if aString is None or aString == "********":
        return False

    raw: bytes
    try:
        raw = base64.b64decode(aString)
    except Exception as error:
        return False

    try:
        if not raw[:8] == b"Salted__":
            return False
    except Exception as e:
        return False

    return True
    

def umask(aString: str, aMask: Optional[Union[str, bytes]]=None) -> str:
    """
    This function is idempotent, umask is only applied to the input if it's
    a base64 encoded string, otherwise the function performs no operation 
    and returns the provided text as provided.
    
    Note that many strings can be accepted as base64 valid input, so this
    funciton idempotented is not warrantied.

    Unmask the provided string, decrypts the provided text to reveal the 
    previously hidden information.

    The algorithm used is AES GCM, this algorithm requires a key and iv,
    these are calculated using the mask, which is passed as part of the 
    b64encoded text to unmask.

    After b64 decoding aString we are left with bytes, the first 8 bytes 
    of the text should be b"Salted__", the following MASK_SIZE bytes are the 
    mask and the rest is the masked/encrypted message.

    Arguments
        aString:str
            A str that can be ascii encoded to bytes. If GCM mode at least 17
            bytes must be sent, since the first 16 are requiredand the rest is
            the message.
        aMask(optional):str=None
            A str, bytes or None. If present must be MASK_SIZE bytes long.
            None  - is the default and results in a randomly generated mask.
            str   - a str that can be ascii encoded to bytes
            bytes - a valid ascii encoded byte array
    """
    if aString is None or aString == "********":
        return aString

    raw: bytes
    try:
        raw = base64.b64decode(aString)
    except Exception as error:
        # If we cannot b64 decode we assume the string was not encoded
        return aString

    try:
        # We look for the "Salted__" to determine the encryption cipher
        if not raw[:8] == b"Salted__":
            # not masked with GCM try ECB for compatibility
            return umask_ecb(aString, aMask)
    except Exception as e:
        # This should not happen, but we enter here we raise an ValueError
        ebLogInfo(f"Encrypted message does not have the required length for ECB. {e}")

    # No matter if encryption is ECB or GCM the resulting masked string will be 
    #at least 16 bytes long because ECB is padded to 16 and GCM contains 
    #"Salted__" plus the mask value of MASK_SIZE bytes (at least 8), at such 
    #aString cannot be less than 16 bytes long.
    if len(raw) < 16:
        raise ValueError("Encrypted message does not have the required length.")

    # aMask validation must at least be MASK_SIZE bytes long
    if aMask and not len(aMask) >= MASK_SIZE:
        raise ValueError(f"aMask must be at least {MASK_SIZE} bytes long.")

    _mask: Optional[Union[str, bytes]] = aMask
    if _mask is None:
        _mask = raw[8:8 + MASK_SIZE]  # get the salt
    elif isinstance(_mask, str):
        #if aMask is provided we ignore the mask on the message itself.
        _mask = _mask.encode("ascii", "ignore")
    elif not isinstance(_mask, bytes):
        raise ValueError("The mask function supports str, bytes or None on the mask argument.")

    # The first 16 bytes are "Salted__" and the mask value (8 bytes)
    #the rest is the encrypted message.
    ciphertext:bytes = raw[16:]

    # At this point _mask is of type bytes and contains bytes
    key, iv = getKeyAndIV(_mask.decode("ascii", "ignore"), _mask)
    _cipher: AESGCM = AESGCM(key)
    decrypted: str = six.ensure_text(_cipher.decrypt(iv, ciphertext, AAD))
    return decrypted


# Deprecated
def umask_ecb(string, mask=None):

    def _get_default_mask():

        _db_path = os.path.join(get_gcontext().mGetBasePath(), "db")
        _wallet_path = os.path.join(_db_path, "cwallet.sso")
        _dbcli_path = os.path.join(get_gcontext().mGetBasePath(), "dbcli")
        _mkstore_path = os.path.join(_dbcli_path, "bin", "mkstore")

        # If mkstore doesn't exist, we create it
        if not os.path.exists(_mkstore_path):

            os.makedirs(_db_path, exist_ok=True)

            _zip_path = os.path.join(get_gcontext().mGetBasePath(), "packages", "wallet_util.zip")
            os.makedirs(_dbcli_path, exist_ok=True)
            mExecuteLocal(["/bin/unzip", _zip_path, "-d", _dbcli_path])

        # Create wallet if it doesn't exist
        if not os.path.exists(_wallet_path):
            mExecuteLocal([_mkstore_path, "-wrl", _db_path, "-createALO"])

        # Get default mask entry or create it if needed
        _default = "mwnq%r^Up>)OMz|[4:5G#jfY\\R+FQN=H"

        _cmd = [_mkstore_path, "-wrl", _db_path, "-viewEntry", "default_mask"]
        _rc, _std_out, _ = mExecuteLocal(_cmd)

        if _rc != 0:
            mExecuteLocal([_mkstore_path, "-wrl", _db_path, "-createEntry", "default_mask", _default])
            _, _std_out, _ = mExecuteLocal(_cmd)

        _pass =  _std_out.strip().split('\n')[-1].strip()
        _pass = _pass.split("=")
        _pass.pop(0)
        _pass = "=".join(_pass).strip()

        return _pass


    if mask is None:
        mask = _get_default_mask()
    mask = mask.encode('ascii')
    backend = default_backend()
    cipher = Cipher(algorithms.AES(mask), modes.ECB(), backend=backend)
    decryptor = cipher.decryptor()
    try:
        ustring = six.ensure_text((decryptor.update(base64.b64decode(string)) + decryptor.finalize()))
    except:
        return string
    
    #remove padding if any 
    if ustring and ustring[-1] == PADDING:
        ustring = ustring.rstrip(PADDING)

    return ustring

def maskSensitiveData(original_dict, sensitive_fields=SENSITIVE_FIELDS, use_mask=True, full_mask=False):
    data_dict = copy.deepcopy(original_dict)
    for key, value in list(data_dict.items()):
        if value is None:
            continue
        if isinstance(value, dict):
            data_dict[key] = maskSensitiveData(value, sensitive_fields, use_mask)
        elif key.lower() in sensitive_fields or 'passwd' in key.lower():
            data_dict[key] = mask(value) if use_mask else '********'
    
    if full_mask:
        data_dict = six.ensure_text(base64.b64encode(pickle.dumps(data_dict)))
    return data_dict

def umaskSensitiveData(original_dict, sensitive_fields=SENSITIVE_FIELDS, full_mask=False):
    data_dict = original_dict
    if full_mask:
        data_dict = pickle.loads(base64.b64decode(data_dict))
    data_dict = copy.deepcopy(data_dict)
    if data_dict is None:
        return None
    for key, value in list(data_dict.items()):
        if value is None:
            continue
        if isinstance(value, dict):
            data_dict[key] = umaskSensitiveData(value, sensitive_fields)
        elif (key.lower() in sensitive_fields or 'passwd' in key.lower()) and len(value) > 0:
            data_dict[key] = umask(value)
    return data_dict

def gen_mask(size=32):
    base = [chr(x) for x in six.moves.range(DLIMIT, ULIMIT)]
    if ASIZE < size:
        base *= size / ASIZE
    random.shuffle(base)
    return ''.join(base[:size])
