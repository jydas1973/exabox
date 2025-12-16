"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    AuthenticationStorage.py

FUNCTION:
    Handle Storage of HTTP Auth credentials

NOTE:
    None

History:
    vgerard    2019/10/04
    
"""

from exabox.core.Context import get_gcontext
from exabox.core.Mask import umask,mask
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogError,ebLogInfo
from enum import Enum
import bcrypt
import base64
import os
import stat
import shutil
import subprocess
import uuid
import json

class ebHttpCredentialType(Enum):
    HASH = 1,
    MASKED = 2,
    LEGACY = 3

class ebGetHTTPAuthStorage(object):
    # Pseudo-Singleton with static variables
    active_storage = None
    cred_type      = None

    def __init__(self, aCredentialPrefix='exacloud_', aCustomStorage=None, aExacloudOpts=None):
        if ebGetHTTPAuthStorage.active_storage == None:
            if not aExacloudOpts:
                aExacloudOpts = get_gcontext().mGetConfigOptions()
            if "wallet_auth" in list(aExacloudOpts.keys()):
                # Valid conf values are either Hash or Masked or Legacy
                ebGetHTTPAuthStorage.cred_type =  ebHttpCredentialType[aExacloudOpts["wallet_auth"].upper()]
                ebGetHTTPAuthStorage.active_storage = ebWalletAuthStorage(aCredentialPrefix)
            else:
                ebGetHTTPAuthStorage.cred_type = ebHttpCredentialType.LEGACY
                # Used for remote management which do not rely on exabox.conf for LEGACY mode
                if aCustomStorage:
                    ebGetHTTPAuthStorage.active_storage = aCustomStorage
                else:
                    ebGetHTTPAuthStorage.active_storage = ebConfigAuthStorage()
    
    # Proxy method
    def mGetCredential(self):
        return ebGetHTTPAuthStorage.active_storage.getCredential()

    def mGetCredentialType(self):
        return ebGetHTTPAuthStorage.cred_type
    
    # This method needs to go away as it prevents full Hash based implementation
    # TODO
    def mGetAdminCredentialForRequest(self):
        _cred = None
        _type = self.mGetCredentialType()
        if   _type == ebHttpCredentialType.HASH:
            raise RuntimeError("Hashed storage do not support building a request")
        elif _type == ebHttpCredentialType.MASKED:
            _cred =  umask(self.mGetCredential()[b'admin'])
        elif _type == ebHttpCredentialType.LEGACY:
            _cred =  self.mGetCredential()[b'admin']
        
        if not _cred:
            raise ValueError('Unsupported Credential type: {}'.format(_type))

        return base64.b64encode(b'admin:'+ _cred).decode('utf-8')

# Authentication Storage:  Interface and 2 implementations 
# ConfigAuth: exabox.conf based
# WalletAuth: wallet based
class ebHTTPAuthStorage(object):
    def getCredential(self):
        return NotImplementedError()
    def getCredentialType(self):
        return NotImplementedError()

class ebBasicAuthStorage(ebHTTPAuthStorage):
    def __init__(self, aBasicStr):
        _auth_str = base64.b64decode(aBasicStr.encode('utf8'))
        _user,_pwd = _auth_str.split(b':',1)
        self.__auth = {_user:_pwd}

    def getCredential(self):
        return self.__auth

class ebConfigAuthStorage(ebHTTPAuthStorage):
    def __init__(self, aExacloudOpts=None):
        if not aExacloudOpts:
            aExacloudOpts = get_gcontext().mGetConfigOptions()
        if "agent_authkey" in list(aExacloudOpts.keys()):
            self.__auth_key = aExacloudOpts["agent_authkey"]
        elif "agent_auth" in list(aExacloudOpts.keys()):
            user, pwd = aExacloudOpts["agent_auth"]
            _user = base64.b64decode(user)
            _pwd  = base64.b64decode(pwd)
            self.__auth = {_user:_pwd}
        else:
            raise ValueError("Configuration must include HTTP authentication parameters")
            
    def getCredential(self):
            return self.__auth


class ebWalletAuthStorage(ebHTTPAuthStorage):
    def __init__(self, aCredentialPrefix='exacloud_', aWalletLoc = os.path.join('config','wallet')):
        _mkstore = os.path.join('dbcli','bin','mkstore')
        try:
            _o = subprocess.check_output([_mkstore,'-wrl',os.path.join(aWalletLoc),'-viewEntry',aCredentialPrefix+'admin'])
            # TODO: Support multiple users by listing credentials and split prefix
            self.__credential = {b'admin':_o.strip().split(b'\n')[-1].split(b'=',1)[-1].strip()}
        except subprocess.CalledProcessError as cpe:
            _err = "Unable to fetch credential from Wallet, non-zero returncode from mkstore: {}".format(cpe.returncode)
            raise KeyError(_err) # Mask the command
        
    def getCredential(self):
        return self.__credential


class ebConvertToWalletStorage(object):
    """ Utility class to convert credential from config file to Wallet """

    def __init__(self, aCredStore, aConfigFile=os.path.join('config','exabox.conf'), 
                       aConfigKeys=('agent_auth','agent_authkey'), aCredentialPrefix='exacloud_'):
        """
            :param ebHTTPAuthStorage aCredStore: 
                An instance of a credential Store
            :param str aConfigFile:
                Path to the configuration file to migrate
            :param iterable aConfigKeys:
                List of configuration keys to remove from aConfigFile
            :param str aCredentialPrefix:
                Prefix to insert credentials from the aCredStore to the Wallet
        """
        _base = get_gcontext().mGetBasePath()
        self.__walletPath = os.path.join(_base, os.path.join('config','wallet'),)
        self.__mkstore = os.path.join(_base,'dbcli','bin','mkstore')
        self.__cred    = aCredStore.getCredential()
        self.__wallet_prefix = aCredentialPrefix
        self.__config_file   = os.path.join(_base,aConfigFile)
        self.__config_keys   = aConfigKeys
        self.__backup_config = None

    def mCheckPrereq(self, aCredType=ebHttpCredentialType.MASKED):
        if aCredType != ebHttpCredentialType.MASKED and aCredType != ebHttpCredentialType.HASH:
            raise ValueError('Unsupported target Credential type: {}'.format(aCredType))

        if os.path.exists(self.__walletPath):
            _err = 'a Wallet file already exists in {}, conversion call do not support pre-existing wallets'.format(self.__walletPath)
            ebLogError(_err)
            raise RuntimeError(_err)
        _db = ebGetDefaultDB()
        _db.mCreateAgentTable() # In case agent was never started
        _agentStatus = _db.mAgentStatus(get_gcontext().mGetConfigOptions()['agent_id'])
        if _agentStatus and _agentStatus[2] == 'running':
            _err = 'Please execute the credential conversion command with Exacloud stopped'
            ebLogError(_err)
            raise RuntimeError(_err)

        return True

    def mDoConversion(self, aCredType=ebHttpCredentialType.MASKED):

        try:
            if not os.path.exists(self.__walletPath):
                ebLogInfo('*** Creating Wallet')
                _o = subprocess.check_output([self.__mkstore,'-wrl',self.__walletPath,'-createALO'])
            # import all users and mask credential before storage
            for user,cred in list(self.__cred.items()):
                ebLogInfo('*** Migrating user {0} credentials to {1}{0}'.format(user.decode('utf8'), self.__wallet_prefix))
                if aCredType == ebHttpCredentialType.MASKED:
                    _walletCred = mask(cred)
                elif aCredType == ebHttpCredentialType.HASH:
                    _walletCred = bcrypt.hashpw(cred,bcrypt.gensalt())
                _o = subprocess.check_output([self.__mkstore,'-wrl',
                                              self.__walletPath,
                                            '-createEntry', 
                                            '{}{}'.format(self.__wallet_prefix,
                                                          user),
                                             _walletCred])

        except subprocess.CalledProcessError as cpe:
            _err = "mkstore command returned a non-zero code({})".format(cpe.returncode)
            ebLogError(_err)
            self.mRollback(1)
            raise RuntimeError(_err) #Do not output the credential in command line
        except:
            self.mRollback(1)
            raise
        
        self.mMigrateConfiguration()

    def mMigrateConfiguration(self, aCredType=ebHttpCredentialType.MASKED):
        _config_file = self.__config_file
        _uuid   = uuid.uuid4()
        _backup = _config_file + '.bak.' + str(_uuid)
        try:
            shutil.copy(_config_file,_backup)
            self.__backup_config = _backup

            with open(_config_file,'r') as _config_fd:
                _config = json.load(_config_fd)

            # Remove current auth keys
            for ck in self.__config_keys:
               _config.pop(ck, None)
            # Add masked key ('mask' or 'hashed' depending on aCredType)
            _config['wallet_auth'] = aCredType.name.lower()
            # Add user write permissions
            _st = os.stat(_config_file)
            if not (_st.st_mode & stat.S_IWRITE):
                ebLogInfo('Added write permission for user to {}'.format(_config_file))
                os.chmod(_config_file, _st.st_mode | stat.S_IWRITE)
            with open(_config_file,'w') as _config_fd:
                json.dump(_config,_config_fd,indent=4)
        except:
            self.mRollback(2)
            raise

    def mRollback(self, aStep=2):
        if aStep == 2 and self.__backup_config:
            ebLogInfo('Rollback: Restore configuration backup')
            shutil.copy(self.__backup_config, self.__config_file)
            aStep = aStep - 1

        if aStep == 1:
            ebLogInfo('Rollback: Deleting wallet')
            shutil.rmtree(self.__walletPath, ignore_errors=True)
    
    def mDeleteBackupConfiguration(self):
        os.remove(self.__backup_config)

