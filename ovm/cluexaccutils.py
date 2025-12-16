"""
 Copyright (c) 2020, Oracle and/or its affiliates. All rights reserved.

NAME:
    cluexaccutils.py -  ExaCC Specific parts that can be shared among modules

FUNCTION:
    Generic part for OCI-ExaCC 

NOTE:

History:

    MODIFIED   (MM/DD/YY)
       vgerard  03/23/20 - Creation 
"""

import json
import socket
import os
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError



class ebOCPSJSONReader(object):
    """
       Class to OCPS JSON parsing
    """
    def __init__(self):
        _ocps_jsonpath = ebAtpUtils.mCheckExaboxConfigOption('ocps_jsonpath')
        if not _ocps_jsonpath or not os.path.exists(_ocps_jsonpath):
            _msg = 'OCI-Exacc requires ocps_jsonpath setting in exabox.conf'
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0120, 0xA, _msg)
        with open(_ocps_jsonpath,'r') as fd:
            self.__ocps_json = json.load(fd)
        
        self.__admin_services = None

    def mGetCPSAdminIps(self):
        # Get CPS Admin IPs
        _cps_admin_ips = []
        for _nodes in self.__ocps_json['servers']:
            _cps_admin_ips.append(_nodes['adminIp'])

        return _cps_admin_ips
        
    def mGetServices(self):
        """
           Return Admin Network Services Info
        """
        # Caching
        if self.__admin_services is not None:
            return self.__admin_services

        _natfsip   = ebAtpUtils.mCheckExaboxConfigOption('nat_fileserver_ip')
        _natfsport = ebAtpUtils.mCheckExaboxConfigOption('nat_fileserver_port')
        _ret       = {}

        if _natfsip:
            #Validate IP and port
            try:
                socket.inet_aton(_natfsip)
            except socket.error:
                raise ExacloudRuntimeError(0x0750, 0xA, 'Invalid IP provided for nat_fileserver_ip parameter', aStackTrace=False)
            if not _natfsport or not _natfsport.isdigit() or not int(_natfsport) <= 65535:
                _natfsport = "2080"
            _ret['fileserver'] = {'ip': _natfsip, 'port': _natfsport}

        
        if  'forwardProxy_ip' in self.__ocps_json and 'forwardProxy_port' in self.__ocps_json:
            _fwd_ip   = self.__ocps_json['forwardProxy_ip']
            _fwd_port = self.__ocps_json['forwardProxy_port']
            try:
                socket.inet_aton(_fwd_ip)
            except socket.error:
                raise ExacloudRuntimeError(0x0750, 0xA,
                        'Invalid IP ({}) provided for forwardProxy_ip in OCPS JSON'
                        .format(_fwd_ip), aStackTrace=False)
            if not _fwd_port or not _fwd_port.isdigit() or not int(_fwd_port) <= 65535:
                raise ExacloudRuntimeError(0x0750, 0xA,
                        'Invalid PORT ({}) provided for forwardProxy_port in OCPS JSON' 
                        .format(_fwd_port), aStackTrace=False)
            _ret['forwardproxy'] = {'ip': _fwd_ip, 'port': _fwd_port}
        
        self.__admin_services = _ret
        return _ret