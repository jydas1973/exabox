"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. All rights reserved.

NAME:
    HTTPAuthentication.py

FUNCTION:
    Handle HTTP Auth during request processing

NOTE:
    None

History:
    vgerard    2019/10/04
    
"""

from exabox.agent.AuthenticationStorage import ebHttpCredentialType
from exabox.core.Context import get_gcontext
from exabox.core.Mask  import umask
from exabox.log.LogMgr import ebLogError
from enum import Enum
import bcrypt
import base64


class ebHTTPAuthResult(Enum):
    """ ebHTTPAuthResults returned by mEvaluateAuth """
    AUTH_NONE  = 1,
    AUTH_ERROR = 2,
    AUTH_OK    = 3


class ebHTTPAuthentication(object):
    """ Store credential and process HTTP Authorization header values """

    def __init__(self, aHTTPCredentialStorage):
        """ 
            Save the extracted credential for efficiency
            :param obj aHTTPCredentialStorage:
                A class implementing ebHTTPAuthStorage base class
        """
        self.__credential = aHTTPCredentialStorage.mGetCredential()
        self.__credentialType = aHTTPCredentialStorage.mGetCredentialType()

    def mEvaluateAuth(self, aAuthorizationHeader):
        """
            Process aAuthorizationHeader against credential
            :param aAuthorizationHeader
                String value ('Basic XXXX') or None
            :return 
                ebHTTPAuthResult Object:
                    ebHTTPAuthResult.AUTH_NO: No Auth header/None provided
                    ebHTTPAuthResult.AUTH_ERROR: Authentication Error
                    ebHTTPAuthResult.AUTO_OK: Authentication Success
        """
        if not aAuthorizationHeader:
            return ebHTTPAuthResult.AUTH_NONE

        _tokens = aAuthorizationHeader.split('Basic ',1)

        if len(_tokens) <= 1: # no token Found, error
            return ebHTTPAuthResult.AUTH_ERROR

        _auth_str = _tokens[1] #Everything after 'Basic '
        _decoded = base64.b64decode(_auth_str).split(b':',1)
        if len(_decoded) == 1:
            return ebHTTPAuthResult.AUTH_ERROR

        _user = _decoded[0]
        _pwd  = _decoded[1]
        
        _auth_result = False
        
        # Check user exists
        if _user not in list(self.__credential.keys()):
            return ebHTTPAuthResult.AUTH_ERROR

        _stored_credential = self.__credential[_user]
        
        # COMPUTE THE ACTUAL AUTHENTICATION depending on Cred type
        if self.__credentialType == ebHttpCredentialType.HASH:
            if _stored_credential[:2] == '$2':
                _auth_result = bcrypt.checkpw(_pwd, self.__credential[_user])
            else:
                raise ValueError('Unsupported type of Hashed Credential')
        elif self.__credentialType == ebHttpCredentialType.MASKED:
            _auth_result = (_pwd == umask(self.__credential[_user]))
        elif self.__credentialType == ebHttpCredentialType.LEGACY:
            _auth_result = (_pwd == self.__credential[_user])
        else:
            raise ValueError('Unsupported type of credential: {}'.format(self.__credentialType))
        

        if not _auth_result:
            return ebHTTPAuthResult.AUTH_ERROR

        return ebHTTPAuthResult.AUTH_OK

