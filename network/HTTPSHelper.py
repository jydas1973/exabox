"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    HTTPSHelper - Functionality for HTTPS and TLS Certificate support

FUNCTION:
    Provide basic/core API for managing HTTPS and TLS certificate validation

NOTE:
    None

History:
    aararora    11/14/2025 - Bug 38638555: Incomplete http requests causing agent to hang and not accept further requests
    aararora    03/12/2024 - Bug 36363054: Exacc is not using client certificate and key file in tls mode
    aararora    02/22/2024 - Bug 36316151: Make https code generic for ExaCC and ExaCS
    aypaul      11/29/2023 - Enh#35730776 Integration of OCI certificate service with exacloud agent.
    aararora    10/19/2023 - Bug 35647494: Add https support for ExaCC
    ndesanto    08/31/2022 - Retrieve tls.conf path from exabox.conf
    ndesanto    11/05/2019 - Create file. ENH 30480538: HTTPS and Certificate Rotation

"""

import base64
import io
import itertools
import json
import os
import socket
import ssl
import sys

from enum import Enum
from http.client import HTTPConnection, HTTPSConnection, HTTPResponse
from six.moves import urllib
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import HTTPSHandler
from typing import Any, ClassVar, Dict, List, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from exabox.config.ebCertificateConfig import ebCertificateConfig
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug,
                                ebThreadLocalLog, ebLogVerbose, ebSetLogLvl,
                                ebLogInit, ebLogFinalize, ebLogCrit, ebLogTrace,
                                ebLogAddDestinationToLoggers, ebLogDeleteLoggerDestination,
                                ebGetDefaultLoggerName)


_UNKNOWN = "UNKNOWN"

def use_oci_certificates() -> bool:
    _mode: bool = False
    _cfg: str = ""

    with open(os.path.join(os.getcwd(),"config/exabox.conf")) as fd:
        _cfg = json.load(fd)

    if "use_ocicerts_https" in _cfg:
        if isinstance(_cfg["use_ocicerts_https"], str):
            _mode = _cfg["use_ocicerts_https"].lower() == "true"

    return _mode


def get_oci_certificates(isClient=False):

    _rootca = None
    _client_cert = None
    _client_key = None
    _cfg = None
    _oci_cert_conf_file = os.path.join(os.getcwd(),"config/oci_certs.conf")

    if not os.path.exists(_oci_cert_conf_file):
        raise Exception(f"OCI certificate configuration doesn't exist at {_oci_cert_conf_file}")
    with open(_oci_cert_conf_file) as _fd:
        _cfg = json.load(_fd)

    _rootca = os.path.join(os.getcwd(), _cfg["rootca_certificate"])
    _https_protocol = _cfg["protocol"]
    if isClient:
        _client_cert = os.path.join(os.getcwd(), _cfg["client_certificate"])
        _client_key = os.path.join(os.getcwd(), _cfg["exacloud_client_key"])
    else:
        _client_cert = os.path.join(os.getcwd(), _cfg["server_certificate"])
        _client_key = os.path.join(os.getcwd(), _cfg["exacloud_server_key"])

    return _rootca, _client_cert, _client_key, _https_protocol

def is_exacs():
    """
    Check if this is exacs environment or not
    - return True if ociexacc is False
    - return False if ociexacc is True
    """
    with open(os.path.join(os.getcwd(), "config/exabox.conf")) as fd:
        _cfg = json.load(fd)
    if "ociexacc" in _cfg and (_cfg["ociexacc"] == True or _cfg["ociexacc"] == "True"):
        return False
    else:
        return True

def is_https_enabled() -> bool:
    _mode: bool = False
    _cfg: str = ""

    with open("./config/exabox.conf") as fd:
        _cfg = json.load(fd)

    if "https_enabled" in _cfg:
        if isinstance(_cfg["https_enabled"], str):
            _mode = _cfg["https_enabled"].lower() == "true"

    return _mode

def is_mtls_enabled_exacc() -> bool:
    _mtls_enabled = False

    with open(os.path.join(os.getcwd(), "config/exabox.conf")) as fd:
        _cfg = json.load(fd)

    if "exacc_mtls" in _cfg:
        if _cfg["exacc_mtls"] == True or _cfg["exacc_mtls"] == "True":
            _mtls_enabled = True

    return _mtls_enabled

def get_tls_config_path() -> str:
    _path: str = "config/tls.conf"
    _cfg: str = ""

    with open("./config/exabox.conf") as fd:
        _cfg = json.load(fd)

    if "default_tls_conf" in _cfg:
        if isinstance(_cfg["default_tls_conf"], str):
            _path = _cfg["default_tls_conf"]

    return _path

def get_ca_cert_path_exacc(app_cfg=None) -> str:
    _path: str = "/etc/pki/ociexacc/cacert.pem"
    _cfg: str = ""

    if app_cfg and "ca_cert_file" in app_cfg:
        _path = app_cfg["ca_cert_file"]
        return _path

    with open(os.path.join(os.getcwd(), "config/exabox.conf")) as fd:
        _cfg = json.load(fd)

    if "exacc_ca_cert_file" in _cfg:
        if isinstance(_cfg["exacc_ca_cert_file"], str):
            _path = _cfg["exacc_ca_cert_file"]

    return _path

def _get_secret() -> str:
    _secret = None
    with open("./config/exabox.conf") as fd:
        _cfg = json.load(fd)

    if "agent_auth" in _cfg:
        _secret = base64.b64decode(_cfg["agent_auth"][1])

    return _secret


def is_secret_required(aCertificateConfig: ebCertificateConfig) -> bool:
    _required = False
    try:
        _key: rsa.RSAPrivateKey = None
        with open(
            aCertificateConfig["client_certificate_key_file"], "rb") as fd:
            load_pem_private_key(
                fd.read(), 
                password=_get_secret)
        _required = True
    except TypeError:
        _required = False
    
    return _required

def get_socket_timeout():
    _cfg: str = ""

    with open(os.path.join(os.getcwd(),"config/exabox.conf")) as fd:
        _cfg = json.load(fd)

    if "agent_socket_timeout" in _cfg and _cfg["agent_socket_timeout"] != "":
        _agent_socket_timeout = _cfg["agent_socket_timeout"]
        return int(_agent_socket_timeout)
    else:
        # default timeout of 15 seconds
        return 15

class ebHttpMethodType(str, Enum):
    POST = "POST",
    GET = "GET",
    PUT = "PUT",
    PATCH = "PATCH",
    DELETE = "DELETE"

    def __str__(self):
        return str(self.value)


class ebResponse(io.BufferedIOBase):
    """ Asynchronous Reponse object, this wraps the actual Reponse object and 
    keeps it API intact, this is done to be able to close the connection and 
    comply with mTLS requirements. """

    def __init__(self, aUrl: str, aHttpresponse: HTTPResponse=None):
        self.aUrl: str = aUrl
        self.headers: Dict[str, Any] = None
        self.msg: str = None
        self.data: str = None
        self.version: int = _UNKNOWN # HTTP-Version
        self.status: int = _UNKNOWN  # Status-Code
        self.reason: str = _UNKNOWN  # Reason-Phrase

        self.chunked = _UNKNOWN         # is "chunked" being used?
        self.chunk_left = _UNKNOWN      # bytes left to read in current chunk
        self.length = _UNKNOWN          # number of bytes left in response
        self.will_close = _UNKNOWN      # conn will close at end of response

        if aHttpresponse:
            self._mSetFromReponse(aHttpresponse)

    def _mSetFromReponse(self, aHttpresponse: HTTPResponse=None) -> None:
        self.headers = aHttpresponse.getheaders()
        self.msg = aHttpresponse.msg
        self.data = aHttpresponse.read()
        if self.data and hasattr(self.data, "decode"):
            self.data = self.data.decode("utf8")
        self.version = aHttpresponse.version
        self.status = aHttpresponse.status
        self.reason = aHttpresponse.reason
        self.chunked = aHttpresponse.chunked
        self.chunk_left = aHttpresponse.chunk_left
        self.length = aHttpresponse.length
        self.will_close = aHttpresponse.will_close

    def fileno(self):
        pass
    
    def seek(self):
        pass
    
    def truncate(self):
        pass
    
    def detach(self):
        pass

    def read(self, size: int=-1):
        if size > -1:
            return self.data[0, size]
        else:
            return self.data

    def read1(self, size: int):
        return self.read(size)

    def write(self):
        pass

    def close(self):
        pass

    def closed(self):
        pass

    def decode(self, aEncoding=None):
        return self.data

    def __str__(self):
        return self.data


def build_opener(aHost: str, aPort: int, aUrl: str, \
    aMethod: Optional[str]=None, aData: Any=None, 
    aHeaders: Dict[str,Any]={}, aTimeout=None) -> ebResponse:
    """
    Wrapper function for urllib.request that adds the 
    ExacloudHTTPSHandler to support HTTPS and Certificate validation.
    """
    _url: str = aUrl
    if is_https_enabled():
        # Automatically convert http urls to https
        if len(_url) > 7 and "http://" == _url[0:7].lower():
            _url = "https://" + _url[7:]

    _timeout: int = socket._GLOBAL_DEFAULT_TIMEOUT
    if aTimeout:
        _timeout = aTimeout

    _request: urllib.request.Request = urllib.request.Request(_url, method=aMethod)
    response: ebResponse = ebResponse(_url)
    _context: Optional[ssl.SSLContext] = None
    if is_https_enabled():
        _https_protocol = None
        _rootca_cert = None
        _client_cert = None
        _client_key = None
        _secret_required = True
        if use_oci_certificates():
            _rootca_cert, _client_cert, _client_key, _https_protocol = get_oci_certificates(isClient=True)
        else:
            app_cfg: ebCertificateConfig = ebCertificateConfig(
                "exacloud", get_tls_config_path())
            _rootca_cert = app_cfg["local_certificate_file"]
            _client_cert = app_cfg["client_certificate_file"]
            _client_key = app_cfg["client_certificate_key_file"]
            _https_protocol = app_cfg["protocol"]
            if is_exacs() or is_mtls_enabled_exacc():
                _secret_required = is_secret_required(app_cfg)

        _context: ssl.SSLContext = ssl.SSLContext(
            getattr(ssl, _https_protocol))
        # The below is in client context, so certificate will always be required
        # Whether it is TLS or MTLS mode.
        if not use_oci_certificates():  
            _context.verify_mode = ssl.CERT_REQUIRED
        else:
            _context.verify_mode = ssl.CERT_NONE

        if not is_exacs():
            # For exacc, ca cert will be a different file than in case of ExaCS
            # since exacloud can be called from multiple places like CPS, ECRA,
            # etc.
            _rootca_cert = get_ca_cert_path_exacc(app_cfg=app_cfg)
        if not use_oci_certificates():
            _context.load_verify_locations(_rootca_cert)
        if is_exacs() or is_mtls_enabled_exacc():
            if _secret_required:
                _context.load_cert_chain(
                    certfile=_client_cert, 
                    keyfile=_client_key,
                    password=_get_secret())
            else:
                _context.load_cert_chain(
                    certfile=_client_cert, 
                    keyfile=_client_key)

    if not aHeaders:
        aHeaders = {}
    aHeaders["User-Agent"] = "python-requests/{}.{}.{}".format(\
        sys.version_info[0], sys.version_info[1], sys.version_info[2])
    for key in aHeaders:
        _request.add_header(key, aHeaders[key])

    _response = urllib.request.urlopen(_request, data=aData, context=_context, timeout=aTimeout)

    response = ebResponse(_url, _response)
    # if response.status != 200:
    #     raise urllib.error.HTTPError(\
    #         _url, response.status, response.msg, None, None)

    return response

