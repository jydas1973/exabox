#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_ilom_pwd.py /main/1 2025/08/11 16:10:09 gparada Exp $
#
# handler_ilom_pwd.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      handler_ilom_pwd.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      This endpoint will reset the password of root user in ilom's 
#      ECRA will send a list of servers/host using a JSON payload.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     07/07/25 - 37996087-jsondisp-reset-ilom-pwd
#    gparada     07/07/25 - Creation
#
# Python libs
import base64
import os
import subprocess
from tempfile import NamedTemporaryFile
from typing import Tuple

# Exacloud libs
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.jsondispatch.jsonhandler import JDHandler
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.utils.node \
    import connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check
from exabox.ovm.clucontrol import exaBoxCluCtrl

class IlomPasswordHandler(JDHandler):
    # EXIT CODES
    SUCCESS = 0
    FAIL = 1

    def __init__(self, aOptions, aRequestObj = None, aDb=None):

        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath(
            "exabox/jsondispatch/schemas/ilom_handler.json"))

        """
        Expected format:
        {
            "jsonconf": {
                "servers": [
                    {
                        "host": "sea201610exdd004.domain.com",
                        "ilomhost": "sea201610exdd004lo.domain..com",
                        "new_sct": "<pwd in base64>"
                    },
                    {
                        "host": "sea201610exdd005.domain.com",
                        "ilomhost": "sea201610exdd005lo.domain.com",
                        "new_sct": "<pwd in base64>"
                    },
                    {
                        "host": "sea201610exdd006.domain.com",
                        "ilomhost": "sea201610exdd006lo.domain.com",
                        "new_sct": "<pwd in base64>"
                    },
                    
                ]
            }
        }
        """            
        
    def mExecute(self) -> Tuple[int, dict]:
        """
        Driver func for iterating over nodes from the payload
        This will NOT require an XML as input (only a payload in JSON format 
        with a predefined JSON Schema)

        :returns: a tuple[int, dict] containing the return code and a dictionary
                  representing the results
        """

        _payload = self.mGetOptions().jsonconf.get("jsonconf").get("servers")

        _ebox = exaBoxCluCtrl(get_gcontext())
        
        _response = {}

        ebLogTrace(f"Destination hosts: {_payload}")
        if len(_payload) == 0:
            _rc = IlomPasswordHandler.FAIL
            _response["reason"] = ("Zero destination hosts.")
            return _rc, _response

        _rc, _response = self.mBulkPasswordReset(_payload)
        
        return _rc, _response

    def mBulkPasswordReset(self, aHosts:dict) -> Tuple[int, dict]:
        """
        Iterate over all server entries in the payload
        Run Ilom Pwd for each one and
        Record return code for each one
        
        Args:
            aHosts (dict): The JSON payload containing the "servers" array.
        """        
        _hosts = aHosts
        _action = "Ilom pwd reset"

        _rc = IlomPasswordHandler.SUCCESS
        _response = {}

        # {"host1":(0,output)}
        _hostRC = {}        
        succHosts = []
        errHosts = []
        
        for _entry in _hosts:
            _hostname = _entry['host']
            _newPwd = None
            if 'new_sct' in _entry:
                _newPwd = _entry['new_sct'] 
            else:
                errHosts.append(_hostname)
                _hostRC[_hostname] = -1
                ebLogError(f"Missing new_sct for {_hostname} in payload.")
                _rc = 1
                continue

            ebLogInfo(f"Start {_action} for ilom of: '{_hostname}'")
            
            _hostRC[_hostname] = self.mResetIlomPassword(_hostname, _newPwd)
                
            if _hostRC[_hostname] != 0:
                errHosts.append(_hostname)
                ebLogInfo(f"{_action} failed for: {_hostname}. Continue.")
                _rc = 1
            else:
                succHosts.append(_hostname)

        # Summarize ALL host were able to RESET the user password for ilom
        if all(ret == 0 for key, (ret) in _hostRC.items()) :
            _rc = IlomPasswordHandler.SUCCESS
            str = f"{_action} succeeded in ALL hosts: {_hosts}"
            _response["success"] = _hosts
            _response["fail"] = errHosts
            _response["reason"] = "Success"
            ebLogInfo(_response)
        else:
            _rc = IlomPasswordHandler.FAIL
            str = f"{_action} failed in hosts: {errHosts}"
            _response["success"] = succHosts
            _response["fail"] = errHosts
            _response["reason"] = "Error"

        return _rc, _response

    def mResetIlomPassword(self, aHost:str, aPwd:str) -> int:
        """
        For a given node, exacloud will connect via ssh and 
        run commands to reset the ilom password
        
        Args:
            aHost (str): The name of the hostname
            aPwd (str): The new secret to apply to ilom as pwd
        """
        _usr = 'root'  
        _pwd = aPwd

        # Adding validation since this value will come from ecra payload
        # See comment/update in the original bug 37996087
        if _pwd is None:
            ebLogError("Missing new_sct value")
            return -1

        # Commands (in order):
        # 'ipmitool sunoem cli "set -script /SP/users/root/ locked=false"'
        # 'ipmitool sunoem cli "set -script /SP/preferences/password_policy/account_lockout/ state=disabled"'
        # 'ipmitool user list 0x02 | grep root | awk '{ print $1 }'
        # 'ipmitool user set <HIDDEN FOR SECURITY REASONS>'

        _host = aHost

        _encoded_command_1 = 'cGFzc3dvcmQ='
        _encoded_command_2 = 'd2VsY29tZTE='

        _secret = _pwd if _pwd else _encoded_command_2
        try:
            _decoded_sct = base64.b64decode(_encoded_command_2).decode("utf-8")
        except Exception as ex:
            ebLogError(ex)
            return -1

        _decoded_sct = base64.b64decode(_secret).decode("utf-8")


        _std_out = subprocess.PIPE
        _std_err = subprocess.PIPE

        with connect_to_host(_host, get_gcontext(), username=_usr) \
            as _node:
            _cmd = 'ipmitool sunoem cli "set -script ' \
                + '/SP/users/root/ locked=false"'
            _node.mExecuteCmdLog(_cmd, aStdOut=_std_out, aStdErr=_std_err)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                return _rc
            
            _cmd = 'ipmitool sunoem cli "set -script ' \
                + '/SP/preferences/password_policy/account_lockout/ ' \
                + 'state=disabled"'
            _node.mExecuteCmdLog(_cmd, aStdOut=_std_out, aStdErr=_std_err)
            _rc = _node.mGetCmdExitStatus()
            if _rc:
                return _rc

            # From this command we should get id in hex for root user in ilom
            _cmd = "ipmitool user list 0x02 | grep root | awk '{ print $1 }'"            
            _rc, _std_out, _ = node_exec_cmd_check(_node, _cmd)
            if _std_out:
                _rootUsr = int(_std_out)
                _hex_user = f'0x{_rootUsr:02x}'
            else:
                return -1

            # Now we set the default password to the hex user
            # Syntax is: ipmitool user set <word1> <user_hexa> <word2>            
            _cmd = 'ipmitool user set ' \
                + base64.b64decode(_encoded_command_1).decode("utf-8") \
                + ' ' + _hex_user + ' '\
                + _decoded_sct
            _node.mExecuteCmdLog(_cmd, aStdOut=_std_out, aStdErr=_std_err)
            _rc = _node.mGetCmdExitStatus()

        return _rc
