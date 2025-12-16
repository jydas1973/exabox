#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/agent/ProxyClient.py /main/4 2021/05/12 19:28:13 ndesanto Exp $
#
# ProxyClient.py
#
# Copyright (c) 2020, 2021, Oracle and/or its affiliates. 
#
#    NAME
#      ProxyClient.py - Proxy URL generation separated from Agent
#
#    DESCRIPTION
#      Class made to separate Proxy from Agent
#      Allowing call to PROXY from bin/exabox.py without referencing a magic agent Global Variable
#
#    NOTES
#      API to send command to proxy
#
#    MODIFIED   (MM/DD/YY)
#    dekuckre    12/08/20 - 32239952: Add UPDATE_STATUS_ACTIVE 
#    vgerard     10/21/20 - Creation
#
import json
from typing import Optional,Tuple
import subprocess
from enum import Enum
from socket import getfqdn


from exabox.core.Core import exaBoxCore
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogAgent
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions

class ProxyOperation(Enum):
    """
    Supported Operations to send to the Proxy from Agent
    When adding an Operation, please add test to tests_proxy_client.py
    """
    REGISTER   = ('register')
    DEREGISTER = ('deregister')
    # Update Operation take key and value, specifing tuple here
    UPDATE_STATUS_SUSPEND   = ('update', ('status', 'Suspend'))
    UPDATE_STATUS_ACTIVE   = ('update', ('status', 'Alive'))

    def __init__(self,
                 op    : str,
                 key_value : Optional[Tuple[str,str]] = None):

        self.__op = op
        self.__kv = key_value

    def getOp(self) -> str:
        return self.__op

    def getKeyValue(self) -> Optional[Tuple[str,str]]:
        return self.__kv

    def __str__(self) -> str:
        return f'ProxyOperation: op:{self.__op}, key_value:{self.__kv}'
    

class ProxyClient():
    """
    Class to send requets to Proxy, without Agent object/global var
    """

    def __init__(self, aTestMode: bool=False ):
        from exabox.agent.Agent import GENERIC,compute_agent_port

        self.__config_opts = get_gcontext().mGetConfigOptions()
        self.__args_opts   = get_gcontext().mGetArgsOptions()
        self.__proxy_port  = self.__config_opts.get('proxy_port',None)
        self.__proxy_host  = self.__config_opts.get('proxy_host',None)
        self.__agent_port  = str(compute_agent_port(self.__config_opts,
                                                    self.__args_opts))
        # Not sure what is the usage, but porting from agent proxy code
        self.__agent_reqtype = self.__config_opts.get('agent_reqtype', GENERIC)
        self.__cache_oeda_version = None

        self.__authkey = ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()
        # the GetVersion method could have been static...Create dummy ctx
        self.__ec_version = '{0}({1})'.format(*(exaBoxCore(None,None).mGetVersion()))
        self.__test_mode = aTestMode


    def mSendOperation(self, aProxyOperation : ProxyOperation):
        from exabox.agent.Agent import ebAgentDaemon

        ebLogAgent('NFO', f'Trying to send a {aProxyOperation} request to exaproxy.')
        _request = f'http://{self.__proxy_host}:{self.__proxy_port}/ecinstmaintenance'

        # Operations must be low volume (register/unregister/suspend), ok to send
        # fields and dynamically get OEDA version as OEDA can be replaced 
        # without bounce
        _context = get_gcontext()
        params = [_context.mGetOEDAPath() + "/install.sh", "-h"]

        sp = subprocess
        p  = sp.Popen(params, stdout=sp.PIPE, stderr=sp.PIPE)
        stdout, stderr = wrapStrBytesFunctions(p).communicate()
        _oeda_version = stdout.split()[-1]


        _form_data={'op'          : aProxyOperation.getOp(),
                    'host'        : getfqdn(),
                    'port'        : self.__agent_port,
                    'version'     : self.__ec_version,
                    'request_type': self.__agent_reqtype,
                    'auth_key'    : str(self.__authkey),
                    'oeda_version': _oeda_version}

        # For update 'key' and 'value'
        _extra_kv = aProxyOperation.getKeyValue()
        if _extra_kv:
            _form_data['key']   = _extra_kv[0]
            _form_data['value'] = _extra_kv[1]

        
        ebLogAgent('NFO', f'Request sent to proxy {_request} with data {_form_data}')

        # Static method of Agent, no coupling

        # TestMode to allow full coverage
        if self.__test_mode:
            return (_request, _form_data)
        else:
            ebAgentDaemon.mPerformRequest(_request, self.__proxy_host, self.__proxy_port, json.dumps(_form_data).encode())
