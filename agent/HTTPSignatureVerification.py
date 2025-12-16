#!/bin/python
#
# $Header: ecs/exacloud/exabox/agent/HTTPSignatureVerification.py /main/8 2024/10/24 19:20:56 ririgoye Exp $
#
# HTTPSignatureVerification.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      HTTPSignatureVerification.py - Verify the HTTP signature for API access control
#
#    DESCRIPTION
#      Certain APIs which have destructive consequences, exacloud will restrict access to the same only to the customer. 
#      Exacloud will verify the http signature in the request headers to make sure that the request is initiated by the customer only. 
#
#    NOTES
#      https://confluence.oraclecorp.com/confluence/display/ExaCM/API+Access+Control+Phase1
#      https://confluence.oci.oraclecorp.com/pages/viewpage.action?spaceKey=DBAAS&title=Gen+2+ExaCC+API+Access+Control
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    10/23/24 - Bug 37197710 - Receive mSearchExaKmsEntries result
#                           as list for ExaKVDB instances
#    aypaul      08/29/24 - Bug#37002424 Determine deployment from CPS host
#                           domain name.
#    aypaul      08/27/24 - Issue#36990212 Add database_prod as an accepted
#                           value for signature verification.
#    aypaul      08/23/24 - Enh#36980715 Endpoint list update for API access
#                           control flow.
#    aypaul      08/13/24 - Enhancement Request 36944071 - UPDATE SERVICE
#                           PRINCIPAL CHECK FOR HTTPS SIGNATURE VERIFICATION
#    aypaul      08/02/24 - Bug#36906041 Remove resize operations from access
#                           control list.
#    aypaul      06/21/24 - Bug#36756810 Disable http signature verification
#                           for dev/qa setups.
#    aypaul      06/12/24 - Creation
#

import base64, os, json, cryptography, re
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.core.Context import get_gcontext
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from exabox.exakms.ExaKmsKVDB import ExaKmsKVDB
from exabox.core.DBStore import ebGetDefaultDB

DEPLOYMENTTYPE_DEV_REGISTRYENTRY = "ociexacc_deploymenttype_dev"

APIACCESS_CONTROL_ENDPOINTS = "apiaccess_control_endpoints"
HTTP_HEADER_EXA_AUTH = "exa-authorization"
HTTP_HEADER_EXA_AUTH_KEYID = "keyId"
HTTP_HEADER_EXA_AUTH_ALGORITHM = "algorithm"
HTTP_HEADER_EXA_AUTH_HEADERS = "headers"
HTTP_HEADER_EXA_AUTH_SIGNATURE = "signature"
HTTP_HEADER_EXA_OPC_PRINCIPAL = "exa-opc-principal"

CLAIMKEY_OPC_CERTTYPE = "ptype"
CLAIMKEY_SVC = "svc"

def insertRestrictedEndpointsInformation():

    _apiaccess_control_restricted_endpoints = [
        "vmgi_delete",
        "deleteservice",
        "vmgi_reshape",
        "storage_resize",
        "partition",
        "add_vm_extra_size"
    ]

    _exakms = ExaKmsKVDB()
    _exakms_entry = _exakms.mBuildExaKmsEntry(APIACCESS_CONTROL_ENDPOINTS, json.dumps(_apiaccess_control_restricted_endpoints))
    _is_successful = _exakms.mInsertExaKmsEntry(_exakms_entry)
    if _is_successful:
        ebLogInfo(" Insertion successful for restricted endpoints information.")
        return True
    ebLogError(" Failed to insert restricted endpoint information.")
    return False


class HTTPSignatureVerify(object):

    def __init__(self, aHttpReq) -> None:
        self.__httpreq = aHttpReq
        self.__ociexacc = get_gcontext().mCheckConfigOption('ociexacc', 'True')
        self.__endpoints = list() #TODO: Fetch the list of endpoints to restrict access. ExaCC: ExaKmsKVDB(Done), ExaCS: OCI SiV
        self.__supported_algorithm = ["rsa-sha256"]
        self.__subheader_info = dict()
        self.__mandatory_subheaders = [HTTP_HEADER_EXA_AUTH_KEYID, HTTP_HEADER_EXA_AUTH_ALGORITHM, HTTP_HEADER_EXA_AUTH_HEADERS, HTTP_HEADER_EXA_AUTH_SIGNATURE]
        self.__current_signature_headers = list()
        self.__is_prod_setup = True
        _db = ebGetDefaultDB()
        if _db.mCheckRegEntry(DEPLOYMENTTYPE_DEV_REGISTRYENTRY):
            self.__is_prod_setup = False

    def mPopulateRestrictedEndpoints(self):
        if not self.__ociexacc:
            return
        else:
            _plaintext_restricted_endpoints = None
            _exakms = ExaKmsKVDB()
            _exakms_entry = _exakms.mSearchEntry(APIACCESS_CONTROL_ENDPOINTS)
            if _exakms_entry:
                _plaintext_restricted_endpoints = _exakms_entry.mCreateValueFromEncData()
            self.__endpoints = json.loads(_plaintext_restricted_endpoints)

    def mCheckPresenceOfExaAuthorizationHeader(self):
        _exa_authorization_header = self.__httpreq.getHeaders().get(HTTP_HEADER_EXA_AUTH, None)
        if _exa_authorization_header is None:
            ebLogError(f" Missing header information for {HTTP_HEADER_EXA_AUTH}. Available headers: {self.__httpreq.getHeaders().keys()}")
            return False
        return True

    def mIsEnvDevQaSetup(self):

        if not self.__is_prod_setup:
            ebLogInfo(f" Skipping http signature verification for Dev/QA setup when {HTTP_HEADER_EXA_AUTH} header is absent.")
            return True
        return False

    def mValidateAndExtractHeaders(self):
        _exa_authorization_header = self.__httpreq.getHeaders().get(HTTP_HEADER_EXA_AUTH)
        
        _exa_authorization_header_kvpairs = _exa_authorization_header.split(",")
        for _exa_authorization_header_kvpair in _exa_authorization_header_kvpairs:
            _sub_header, _sub_header_value = _exa_authorization_header_kvpair.split('=', 1)
            if _sub_header_value.startswith('"') and _sub_header_value.endswith('"'):
                _sub_header_value = _sub_header_value[1:-1]
            if _sub_header in self.__mandatory_subheaders:
                ebLogInfo(f" HTTP header {HTTP_HEADER_EXA_AUTH}, subheader {_sub_header} -> {_sub_header_value}")
                self.__subheader_info[_sub_header] = _sub_header_value

        for _mandatory_subheader in self.__mandatory_subheaders:
            if self.__subheader_info.get(_mandatory_subheader, None) is None:
                ebLogError(f" Missing mandatory sub header information for {_mandatory_subheader}")
                return False
            
            if HTTP_HEADER_EXA_AUTH_ALGORITHM == _mandatory_subheader:
                _current_encryption_algorithm = self.__subheader_info.get(HTTP_HEADER_EXA_AUTH_ALGORITHM)
                if _current_encryption_algorithm not in self.__supported_algorithm:
                    ebLogError(f" Unsupported authentication algorithm {self.__subheader_info.get(HTTP_HEADER_EXA_AUTH_ALGORITHM)}")
                    return False
                
            if HTTP_HEADER_EXA_AUTH_HEADERS == _mandatory_subheader:
                _current_signature_headers_composite = self.__subheader_info.get(HTTP_HEADER_EXA_AUTH_HEADERS)
                self.__current_signature_headers = _current_signature_headers_composite.split(" ")
                for _current_signature_header in self.__current_signature_headers:
                    if _current_signature_header.startswith("("):
                        continue
                    if self.__httpreq.getHeaders().get(_current_signature_header, None) is None:
                        ebLogError(f" Missing http header information for {_current_signature_header} required for signature verification.")
                        return False
                    
        ebLogInfo(" HTTP header verification successful.")
        return True         

    def mGenerateExaCCHTTPSignature(self):
        if not self.__ociexacc:
            return None
        
        _complete_http_requestline = self.__httpreq.getRequestLine()#POST /CLUCtrl/sim_install HTTP/1.1
        split_values = re.split(r"HTTP", _complete_http_requestline)
        _simpletext_signature = split_values[0].rstrip()
        for _current_signature_header in self.__current_signature_headers:
            if _current_signature_header.startswith("("):
                continue
            _simpletext_signature += " " + self.__httpreq.getHeaders().get(_current_signature_header)

        ebLogInfo(f" Generated simpletext signature: {_simpletext_signature}")
        return _simpletext_signature

    def mVerifySignatureExaCC(self, aPlainTextSignature):
        _plaintext_signature = aPlainTextSignature
        _received_http_signature = self.__subheader_info.get(HTTP_HEADER_EXA_AUTH_SIGNATURE)

        _bytes_public_key = None
        _wsclient_folder = get_gcontext().mCheckConfigOption('wsclient_sessionkeypath')
        _wsclient_session_key_path = os.path.join(_wsclient_folder, self.__subheader_info.get(HTTP_HEADER_EXA_AUTH_KEYID))
        with open(_wsclient_session_key_path, 'rb') as _fd:
            _bytes_public_key = _fd.read()
        _public_key = load_pem_public_key(_bytes_public_key)

        _bytes_signature = base64.b64decode(_received_http_signature.encode())
        try:
            _public_key.verify(signature=_bytes_signature, data=_plaintext_signature.encode(), padding=padding.PKCS1v15(), algorithm=hashes.SHA256())
        except cryptography.exceptions.InvalidSignature as _crypt_invalid_sigex:
            ebLogError(f" HTTP signature verification has failed. Reason: {_crypt_invalid_sigex}")
            return False
        except Exception as _ex:
            ebLogError(f" Generic exception during http signature verification. Reason: {_ex}")
            return False

        ebLogInfo(" HTTP signature successfully verified.")
        return True

    def mValidateExaOPCPrincipal(self):
        if not self.__ociexacc:
            return True

        _str_exaopc_principal = self.__httpreq.getHeaders().get(HTTP_HEADER_EXA_OPC_PRINCIPAL, None)
        if _str_exaopc_principal is None:
            ebLogError(f" Header value for {HTTP_HEADER_EXA_OPC_PRINCIPAL} does not exist.")
            return False

        _verification_dict = {CLAIMKEY_OPC_CERTTYPE:[None, ["service"]], CLAIMKEY_SVC:[None, ["database", "database_preprod"]]}
        _verification_keys = _verification_dict.keys()
        _exaopc_principal_dict = json.loads(_str_exaopc_principal)
        _list_of_claims = _exaopc_principal_dict.get("claims", [])
        for _claim in _list_of_claims:
            _claim_key = _claim.get("key", None)
            _claim_value = _claim.get("value", None)
            if _claim_key in _verification_keys:
                _verification_dict[_claim_key][0] = _claim_value

        for _claim_key in _verification_keys:
            if _verification_dict[_claim_key][0] is None:
                ebLogError(f" exa-opc-principal key {_claim_key} is absent.")
                return False
            if _verification_dict[_claim_key][0] not in _verification_dict[_claim_key][1]:
                ebLogError(f" Value of exa-opc-principal claim key {_claim_key}, value: {_verification_dict[_claim_key][0]} doesn't match with list of prerequisite values {_verification_dict[_claim_key][1]}")
                return False

        ebLogInfo(f" exa-opc-principal claim keys ({_verification_keys}) successfully validated.")
        return True

    def mCheckIfApiAccessRestricted(self):
        if not self.__ociexacc:
            return False

        _complete_http_requestline = self.__httpreq.getRequestLine()#POST /CLUCtrl/sim_install HTTP/1.1
        split_values = re.split(r"HTTP", _complete_http_requestline)
        _request_target = split_values[0].rstrip()#POST /CLUCtrl/sim_install
        _api_endpoint = _request_target.split(" ")[1]

        for _endpoint in self.__endpoints:
            if _endpoint in _api_endpoint:
                ebLogInfo(f" API endpoint {_api_endpoint} is access restricted using HTTP signature verification.")
                return True

        ebLogInfo(f" API endpoint {_api_endpoint} is not access restricted. Skipping HTTP signature verification.")
        return False

    def mVerifySignature(self):

        self.mPopulateRestrictedEndpoints()

        if not self.__ociexacc:
            ebLogInfo(" HTTP Signature verification is not enabled for ExaCS deployment.")
            return True
        else:
            if not self.mCheckIfApiAccessRestricted():
                return True
            if not self.mCheckPresenceOfExaAuthorizationHeader():
                return self.mIsEnvDevQaSetup()
            if not self.mValidateAndExtractHeaders():
                return False
            _plaintext_http_signature = self.mGenerateExaCCHTTPSignature()
            if not self.mVerifySignatureExaCC(_plaintext_http_signature):
                return False
            if not self.mValidateExaOPCPrincipal():
                return False

            ebLogInfo(f" HTTP signature successfully validated for {self.__httpreq.getRequestLine()}")
            return True
