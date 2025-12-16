#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_user_keys.py /main/7 2025/09/18 15:24:55 gparada Exp $
#
# handler_user_keys.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      handler_user_keys.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     07/15/25 - 38145249 Need to consider DomUs in ExaCC ADB
#    gparada     04/14/25 - 37828983 ssh CPS' as ecra usr, exec cmds with sudo
#    gparada     11/21/24 - 37260301 Handle Warning on secscan create in CPS
#    aararora    11/08/24 - 37260328 Chmod 400 to secscan private key
#    gparada     06/14/24 - 36628459 Handle ssk keys for secscan user
#    gparada     06/14/24 - Creation
#

# Python libs
import os
from tempfile import NamedTemporaryFile
from typing import Tuple

# Exacloud libs
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.userutils import ebUserUtils
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check
from exabox.ovm.clucontrol import exaBoxCluCtrl

class UserHandler(JDHandler):
    # EXIT CODES
    SUCCESS = 0
    FAIL = 1

    ACTION_INJECT = 'inject'
    ACTION_DELETE = 'delete'

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/user_handler.json"))

        """
        Expected format:
        {
            "user_handler":
            {
                "user":
                {
                    "id":"secscan",
                    "action":"inject",
                    "create_user":true,              
                }
            }
        }
        """            
        
    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func for iterating over nodes to create secscan user
        This will NOT require an XML as input (only a payload in JSON format 
        with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _payload = self.mGetOptions().jsonconf.get("user_handler")
        _action = _payload.get("user").get("action")
        _user = _payload.get("user").get("id")
        _createFlag = _payload.get("user").get("create_user")

        _ebox = exaBoxCluCtrl(get_gcontext())

        _rc = 0
        _response = {}
        _response["reason"] = ""
        _priv_key = '/etc/ssh-keys/secscan.priv'

        nodeTypes = [ExaKmsHostType.DOM0,ExaKmsHostType.CELL]
        if _ebox.isATP():
            nodeTypes.append(ExaKmsHostType.DOMU)

        self.infraNodes = self.mGetDestinationHosts(nodeTypes)
        destHosts = [] 
        destHosts += self.infraNodes 
        destCPSHosts = []

        ebLogInfo(f"Add Remote CPS to destinations.")
        _remoteCps = get_gcontext().mCheckConfigOption('remote_cps_host')
        if _remoteCps:
            destCPSHosts.append(_remoteCps)
            destCPSHosts.append("localhost")

        ebLogTrace(f"Destination hosts: {destHosts}")
        if len(destHosts) == 0:
            _rc = UserHandler.FAIL
            _response["reason"] = ("""Zero destination hosts. """
                """No entries in exassh for dom0's or cell's.""")
            return _rc, _response

        if _action == UserHandler.ACTION_INJECT:
            _rc, _response = self.mRemoveKeyInCPS(_ebox, _priv_key)
            if _rc > 0:
                return _rc, _response

            # If user exists, do nothing.
            # _rc, _response = self.mCreateUserInCPS(_ebox,_user)            
            
            _key = self.mGenerateKey()

            _responseInfraNodes = {}
            _rc, _responseInfraNodes = self.mCreateUser(destHosts,_user,_key)

            _responseCPS = {}
            _rc, _responseCPS = self.mCreateUser(destCPSHosts,_user,_key,True)

            _success = _responseInfraNodes["success"] + _responseCPS["success"]
            _fail = _responseInfraNodes["fail"] + _responseCPS["fail"]            
            _response["reason"] = \
                f"User creation: Success on {_success}, Fail on {_fail}."

        elif _action == UserHandler.ACTION_DELETE:
            _rc, _response = self.mRemoveKeyInCPS(_ebox, _priv_key)
            if _rc > 0:
                return _rc, _response

            _responseInfraNodes = {}
            _rc, _responseInfraNodes = self.mDeleteUser(destHosts,_user)            
            if _rc:
                ebLogWarn(f"Warning deleting user {_user} in nodes.")

            _responseCPS = {}
            _rc, _responseCPS = self.mDeleteUser(destCPSHosts,_user,True)
            if _rc:
                ebLogWarn(f"Warning deleting user {_user} in CPS nodes.")

            _success = _responseInfraNodes["success"] + _responseCPS["success"]
            _fail = _responseInfraNodes["fail"] + _responseCPS["fail"]            
            _response["reason"] = \
                f"User deletion: Success on {_success}, Fail on {_fail}."

            # _rc, _response = self.mDeleteUserInCPS(_ebox,_user)            
            # if _rc:
            #     ebLogWarn(f"Warning deleting user {_user} in CPS.")

        else:
            _rc = UserHandler.FAIL
            _response["reason"] = ("Invalid action")
            
        if _rc > 0:
            return _rc, _response                    
 
        if _action == UserHandler.ACTION_INJECT:
            # Create local tmp file with Private Key
            # and copy it to the dom0
            with NamedTemporaryFile(mode='w', delete=True) as _tmp_file:
                _tmp_file.write(_key["private_key"])
                _tmp_file.flush()
                _cmd = f'sudo cp {_tmp_file.name} {_priv_key}'
                _rc1, _i, _o, _e = _ebox.mExecuteLocal(_cmd)
                ebLogInfo(f"cmd: {_cmd}. RC: {_rc1}")

            _cmd = f"sudo chmod 400 {_priv_key}"
            _rc1, _i, _o, _e = _ebox.mExecuteLocal(_cmd)
            ebLogInfo(f"cmd: {_cmd}. RC: {_rc1}")
            if _rc1 > 0:
                _response["reason"] = _response["reason"] + \
                    f" - {_priv_key} could not change permissions. "

            ebLogInfo(f"Stored new priv key: {_priv_key}")

        _rc = UserHandler.SUCCESS   

        return _rc, _response

    def mGetDestinationHosts(self, nodeTypes:list) -> list:
        exakms = get_gcontext().mGetExaKms()
        entries = exakms.mSearchExaKmsEntries({},aRefreshKey=True)
        destHosts = []
        for entry in entries:            
            if entry.mGetHostType() in nodeTypes:                
                ebLogInfo(f"entry: {entry.mToJsonMinimal()}")
                ebLogInfo(f"entry: {entry.mGetFQDN()}")
                if entry.mGetUser() == "root":
                    destHosts.append(entry.mGetFQDN().split(".")[0])
        return destHosts

    def mGenerateKey(self) -> dict:
        # Generate ssh key
        _generatedKeys = {}
        _dummyEntry = ebUserUtils.mCreateSshKeys("opc")
        _generatedKeys["private_key"] = _dummyEntry.mGetPrivateKey()
        _generatedKeys['public_key'] = _dummyEntry.mGetPublicKey("TEMPORAL_KEY")        
        ebLogTrace(f"Priv key {_generatedKeys['private_key']}")
        ebLogTrace(f"Pub key {_generatedKeys['public_key']}")
        return _generatedKeys

    def mCreateUserInCPS(self, aCluControl, aUser:str):
        _ebox = aCluControl
        _user = aUser
        _rc1 = 0
        _response = {}
        ebLogInfo(f"Start. Create User: {_user} in CPS.")

        # In local (CPS), if user does not exist, then add user.
        _getent_cmd = "/usr/bin/getent"
        _useradd_cmd = "/usr/sbin/useradd"

        # Check if secscan user exists
        ebLogInfo(f"cmd: {_getent_cmd} passwd {_user}")
        _rc1, _i, _o, _e = _ebox.mExecuteLocal(f"{_getent_cmd} passwd {_user}")
        ebLogInfo(f"Validate {_user} in CPS. RC: {_rc1}")

        if _rc1 == 0:
            ebLogInfo(f"User already exist, no need to create.")
        else:
            ebLogInfo(f"User does not exist, will be created.")
            _user_add_cmd = \
                f"sudo {_useradd_cmd} '{_user}'"
            _rc1, _i, _o, _e = _ebox.mExecuteLocal(_user_add_cmd)
            ebLogInfo(f"cmd: {_user_add_cmd}")
            ebLogInfo(f"Create User: {_user} in CPS. RC: {_rc1}")
            if _rc1 > 0:
                _response["reason"] = (f" - CPS already have {_user} created. ")
            if _e:
                ebLogError(f"Errors occured while executing {_user_add_cmd} {_e}")

        ebLogInfo(f"End. Create User: {_user} in CPS. RC {_rc1}.")
        return _rc1, _response

    def mDeleteUserInCPS(self, aCluControl, aUser:str):
        _ebox = aCluControl
        _user = aUser
        _rc1 = 0
        _response = {}
        ebLogInfo(f"Start. Delete User: {_user} in CPS.")

        # In local (CPS), if user does not exist, then add user.
        _getent_cmd = "/usr/bin/getent"
        _userdel_cmd = "/usr/sbin/userdel"

        # Check if secscan user exists
        ebLogInfo(f"COMMAND: {_getent_cmd} passwd {_user}")
        _rc1, _i, _o, _e = _ebox.mExecuteLocal(f"{_getent_cmd} passwd {_user}")
        ebLogInfo(f"Validate {_user} in CPS before removing. RC: {_rc1}")

        if _rc1 == 0:
            ebLogInfo(f"User already exist, will be deleted.")
            ebLogInfo(f"COMMAND: {_userdel_cmd} {_user}")
            _rc1, _i, _o, _e = _ebox.mExecuteLocal(f"{_userdel_cmd} {_user}")
        else:
            ebLogInfo(f"User does not exist, no need to remove.")
        ebLogInfo(f"End. Delete User: {_user} in CPS. RC {_rc1}.")
        return _rc1, _response

    def mRemoveKeyInCPS(self, aCluControl, aPrivKey:str):
        _ebox = aCluControl
        _priv_key = aPrivKey
        _rc1 = 0
        _response = {}        

        # In local (CPS), make sure private key is new        
        ebLogInfo(f"Start. Remove Key in CPS: {_priv_key}")

        _cmd = f"sudo /usr/bin/ls {_priv_key}"
        _rc1, _i, _o, _e = _ebox.mExecuteLocal(_cmd)
        if _rc1 > 0:
            _response["reason"] = (f"{_priv_key} not found. No need to delete.")
            # Continue safely
            _rc1 = 0
        else:
            _cmd = f"sudo /bin/rm -rf {_priv_key}"
            _rc1, _i, _o, _e = _ebox.mExecuteLocal(_cmd)
            ebLogInfo(f"cmd: {_cmd}. RC: {_rc1}")
            if _rc1 > 0:
                _response["reason"] = (f"{_priv_key} could not be deleted. ")
        
        ebLogInfo(f"End. Remove Key in CPS: {_priv_key}. RC {_rc1}.")
    
        return _rc1, _response

    def mCreateUser(self, 
                    aDestHosts:list, 
                    aUser:str, 
                    aKey:dict, 
                    aIsCPS:bool=False):
        _destHosts = aDestHosts
        _user = aUser
        _key = aKey
        _rc = 0
        _response = {}
        _usr = 'root' if not aIsCPS else 'ecra'

        # {"host1":(0,output)}
        _hostRC = {}
        for host in _destHosts:
            
            with connect_to_host(host, get_gcontext(), username=_usr) as _node:
                ebLogTrace(f"Check if {_user} exists on {host}")
                _secscan_uid = ebUserUtils.mSearchSecScanUser(_node)

                _home_ssh_dir = f"/home/{_user}/.ssh"
                _home_ssh_auth_dir = ""

                if host in self.infraNodes:
                    _home_ssh_auth_dir = f"{_home_ssh_dir}/authorized_keys"                   
                else:
                    _home_ssh_auth_dir = "/etc/ssh-keys/secscan"

                _extra_cmd = f"sudo /usr/bin/passwd -l {_user};" # expire password

                _extra_cmd += f"sudo /usr/bin/mkdir -p  {_home_ssh_dir};"
                _extra_cmd += f"sudo /usr/bin/chmod 700 {_home_ssh_dir};"
                _extra_cmd += f"sudo /usr/bin/chown {_user}:{_user} {_home_ssh_dir};"

                _extra_cmd += f"sudo /usr/bin/touch {_home_ssh_auth_dir};"
                _extra_cmd += f"sudo /usr/bin/chmod 600 {_home_ssh_auth_dir};"
                _extra_cmd += f"sudo /usr/bin/chown {_user}:{_user} {_home_ssh_auth_dir};"

                _extra_cmd += f"sudo /usr/bin/echo '{_key['public_key']}' | "
                _extra_cmd += f"sudo /usr/bin/tee -a {_home_ssh_auth_dir};"

                ebLogInfo(f"Started user creation for: '{_user}' in {host}")
                ebLogInfo(f"Commands: {_extra_cmd}")

                # mCreateUser returns a tuple
                _hostRC[host] = ebUserUtils.mCreateUser(
                    _node, _secscan_uid, _user, _extra_cmd)
                
                if _hostRC[host][0] != 0:
                    ebLogInfo(f"User creation failed on: {host}. Abort.")                    
                    break

        # Ensure ALL host were able to CREATE the user
        # On failure, UNDO all.
        succHosts = []
        errHosts = []

        if all(ret == 0 for key, (ret, _, _) in _hostRC.items()) :
            _rc = UserHandler.SUCCESS            
            _response["success"] = aDestHosts
            _response["fail"] = errHosts
            ebLogInfo(_response)

        if _rc:
            for key, value in _hostRC.items():
                if value > 0:
                    errHosts.append(key)
                    ebLogInfo(f"User creation to undo over: {errHosts}")
                else:
                    succHosts.append(key)
            # Call Undo        
            _del_rc = self.mDeleteUser(errHosts,_user)
            _rc = UserHandler.FAIL
            _response["success"] = aDestHosts
            _response["fail"] = errHosts
            ebLogWarn(_response)
            return _rc, _response            
                
        return _rc, _response

    def mDeleteUser(self, aDestHosts:list, aUser:str, aIsCPS=False):
        _destHosts = aDestHosts
        _user = aUser
        _rc = 0
        _response = {}
        _usr = 'root' if not aIsCPS else 'ecra'

        # {"host1":(0,output)}
        _hostRC = {}
        succHosts = []
        errHosts = []
        for host in _destHosts:

            with connect_to_host(host, get_gcontext(), username=_usr) as _node:
                ebLogInfo(f"Started user deletion for: '{_user}' in {host}")

                _hostRC[host] = ebUserUtils.mDeleteUser(_node, _user)
                
                if _hostRC[host][0] != 0:
                    errHosts.append(host)
                    ebLogInfo(f"User deletion failed on: {host}. Continue.")
                    _rc = 1
                else:
                    succHosts.append(host)

        # Ensure ALL host were able to DELETE the user
        if all(ret == 0 for key, (ret, _, _) in _hostRC.items()) :
            _rc = UserHandler.SUCCESS
            str = f"User deletion succeeded in ALL hosts: {aDestHosts}"
            _response["success"] = aDestHosts
            _response["fail"] = errHosts
            ebLogInfo(_response)
        else:
            _rc = UserHandler.FAIL
            str = f"User deletion failed in hosts: {errHosts}"
            _response["success"] = succHosts
            _response["fail"] = errHosts

        return _rc, _response

