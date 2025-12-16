"""
 Copyright (c) 2018, 2020, Oracle and/or its affiliates. All rights reserved.

NAME:
    atpendpoints.py - Exacloud Endpoints specific to ATP

FUNCTION:
    Regroup ATP specific endpoints

NOTE:

History:

    MODIFIED   (MM/DD/YY)
       vgerard  09/06/19 - Creation 
"""

import socket
import json
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.ovm.atp import DB_ROUTE_PATH
from exabox.ovm.AtpUtils import ebAtpUtils

"""
  Json specification:

This endpoint add N routes to N CIDR (can be an single IP)
Each CIDR can specify a set of hosts for which /etc/hosts entries
are eventually added if host does not resolve (or if it is forced)

{
'routes':
  [
      {    'cidr': 'CIDR'  
(OPTIONAL) 'hostinfo' :
         [
           { 'ip': <IPinCIDR>,
             'domainname': <fqdn>,
   (OPTIONAL)'write_hostfile': 'force'|'auto'(default)
            }, (0..N)
         ]
       } ,(1..N) 
   ] 
}

Current Usecase: DG
  Example for primary:
     * CIDR is the Secondary Management Subnet (so route is added)
     * one hostinfo is provided, the SCANIP so it is inserted into /etc/hosts
"""

class ATPDomUExecution(object):
    def mExecute(self, aStaging, aDomUs):
        _cmds = aStaging.getCommands()
        ebLogInfo('*** ATPAddBackupRoutes: Executing {} commands'.format(len(_cmds)))
        for _domU in aDomUs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(_domU)
            ebLogInfo('***ATPAddBackupRoutes Setting up routes and hosts on {}'\
                      .format(_domU))
            for _cmd in _cmds:
                _node.mExecuteCmd(_cmd)
            _node.mDisconnect()

#Main Class
class ATPAddBackupRoutes(object):

    def __init__(self, aJSON, aDebug=False):
        self.__json      = aJSON
        self.__debug     = aDebug
        self.mValidateInput()
        self.__routeList = []
        self.mInitializeAllRoutes() #Also syntax check all routes

    def mValidateInput(self):
        if not self.__json:
            raise ValueError('[ATPAddBackupRoutes] JSON Payload is required')
        try:
            #Basic Sanity Check
            self.__json["routes"][0]["cidr"]
        except:
            raise ValueError('[ATPAddBackupRoutes] Invalid JSON Payload')

    def mInitializeAllRoutes(self):
        for _route in self.__json["routes"]:
            _cidr = _route.get('cidr')
            if not _cidr:
                raise ValueError(\
                     '[ATPAddBackupRoutes] Invalid JSON Payload: No "cidr" in route')
            self.__routeList.append(ATPBackupRoute(_cidr, _route.get('hostinfo')))

    # ONLY External API apart of the constructor
    # Optional ExecClass argument for unit testing
    def mExecute(self, aDomUs, aBackupIf, aExecClass=ATPDomUExecution()):
       # Create command staging object    
        _staging = ATPOperationsStaging(aBackupIf)
        for _route in self.__routeList:
            _rc = _route.mExecute(_staging)
            if _rc:
                raise ExacloudRuntimeError(0x0655, 0xA,\
                      'Error during execution of add_atpbackup_route for following route: {}'\
                      .format(_route))
        if self.__debug:
            ebLogDebug('*** ATPAddBackupRoutes *** Staged commands: {}'.format(\
                       '\n'.join(_staging.getCommands())))

        aExecClass.mExecute(_staging, aDomUs)


class ATPBackupRoute(object):
    def __init__(self, aCIDR, aHostInfo):
        self.__cidr     = aCIDR.strip()
        self.__ipFamily = None
       
        self.mValidateCIDR()

        if aHostInfo:
            self.__hostInfo = ATPBackupRouteHostInfo(aHostInfo)
        else:
            self.__hostInfo = None

    def mExecute(self, aStaging):
        aStaging.routeAdd(self.__cidr)
        if self.__hostInfo:
            self.__hostInfo.mExecute(aStaging)

    def mValidateCIDR(self):
        try:
            ip, cidrmask = self.__cidr.split('/')
            cidrmask     = int(cidrmask)
        except:
            raise ValueError('[ATPBackupRoute] CIDR ({}) is invalid'.format(self.__cidr))
        self.__ipFamily = ATPBackupRoute.mValidateIP(ip)
        # Here we have a valid IP, verify CIDRmask range
        validMax={socket.AF_INET:32, socket.AF_INET6:128}
        if (cidrmask < 0 or cidrmask > validMax[self.__ipFamily]):
            raise ValueError('[ATPBackupRoute] CIDR subnet out of range: ({})'.format(self.__cidr))

    @staticmethod
    #returns AF Family or raise ValueError
    def mValidateIP(aIP):
        try:
            socket.inet_pton(socket.AF_INET, aIP)
            return socket.AF_INET
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, aIP)
                # Remove Below raise to allow IPv6 (rest of endpoint should work)
                raise ValueError('[ATPBackupRoute] IPv6 is not yet supported in ECRA')
                return socket.AF_INET6
            except socket.error:
                raise ValueError('[ATPBackupRoute] Invalid IP address in CIDR: ({})'.format(aIP))

class ATPBackupRouteHostInfo(object):
    def __init__(self, aHostInfo):
        self.__hostInfo = aHostInfo
        # List of ip,fqdn,mode [(ip1,fqdn1,'auto'),(ip2,fqdn2,'force'),...]
        self.__hostInfoList = []
        self.mValidateHostInfoList()

    def mExecute(self, aStaging):
        for ip, fqdn, mode in self.__hostInfoList:
            aStaging.hostEntryAdd(ip,fqdn,mode)

    def mValidateHostInfoList(self):
        if not self.__hostInfo:
            return #no HostInfo
        for _host in self.__hostInfo:
            self.__hostInfoList.append(self.mValidateHostInfo(_host))

    def mValidateHostInfo(self,aHost):
        try:
            ip   = aHost['ip']
            fqdn = aHost['domainname'].strip()
        except:
            raise ValueError('[ATPBackupRoute] Invalid Host info, both ip and domainname are required')
        ATPBackupRoute.mValidateIP(ip)
        if len(fqdn) == 0:
            raise ValueError('[ATPBackupRoute] Invalid Domainname for IP: ({})'.format(ip))
        if 'write_hostfile' in aHost:
            write_mode = aHost['write_hostfile']
            if not (write_mode == 'force' or write_mode == 'auto'):
                raise ValueError('[ATPBackupRoute] Invalid Value for write_hostfile option for IP: ({})'.format(ip))
        else:
            write_mode = 'auto'
        return ip,fqdn,write_mode


class ATPOperationsStaging(object):
    # For unit testing, allow to specify another class to execute/verify operation
    def __init__(self, aBackupIf):
        self.__backupIf = aBackupIf
        self.__cmds     = []

    def routeAdd(self, aCidr):
        _ip, _mask = ebAtpUtils.cidr_to_netmask(aCidr)
        _cmd = '{dbroute} add -net {ip} netmask {mask} dev {bkIf}'.format(\
               ip=_ip, mask=_mask, bkIf=self.__backupIf,\
               dbroute=DB_ROUTE_PATH)
        self.__cmds.append(_cmd)

    def hostEntryAdd(self, aIp, aFqdn, aMode):
        _etcHostline = '{ip} {fqdn}'.format(ip=aIp, fqdn=aFqdn)
        _cmd  = ''
        if (aMode == 'auto'):
            _cmd += 'dig +search +short {fqdn} || '.format(fqdn=aFqdn)

        #Look for ip+space(to not match .100 for .10), escape .
        _cmd += 'grep -qe "{}\s" /etc/hosts || echo "{}" >> /etc/hosts'.format(aIp.replace('.','\.'), _etcHostline) 
        self.__cmds.append(_cmd)

    def getCommands(self):
        return self.__cmds
 
