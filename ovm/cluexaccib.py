"""
 Copyright (c) 2018, 2025, Oracle and/or its affiliates. 

NAME:
    cluexaccib.py - Exacloud IB logic, specific to exacc OCI

FUNCTION:
    Setup CPS IB

NOTE:

History:

    MODIFIED   (MM/DD/YY)
       rajsag   12/01/20 - create service prevmsetup error in script
                           ociexacc-cps-setupib.sh
       vgerard  07/06/19 - Creation 
"""

import ipaddress
import subprocess
import socket
import string
import json
import os
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
# Shell secure quoting is implemented in a different module in p2 and p3
from six.moves import shlex_quote


class ExaCCIB_DomU(object):
    def __init__(self, aDomUs, aDebug=False, aMode=False):
        self.__domUs  = aDomUs
        self.__debug  = aDebug
        self.__aMode  = aMode
        _ocps_jsonpath = ebAtpUtils.mCheckExaboxConfigOption('ocps_jsonpath')
        if not _ocps_jsonpath or not os.path.exists(_ocps_jsonpath):
            _msg = 'OCI-Exacc requires ocps_jsonpath setting in exabox configuration for Infiniband Setup'
            raise ExacloudRuntimeError(0x0120, 0xA, _msg)
        with open(_ocps_jsonpath,'r') as fd:
            self.__ocps_json  = json.load(fd)
        self.__ib_domu_ports = ebAtpUtils.mCheckExaboxConfigOption('ib_domu_ports')


    def mSecureDomUIB(self):
        if not self.__ib_domu_ports:
            ebLogInfo('*** OCIEXACC, no ib_domu_ports specified, skipping domU Iptables')
            return True

        ebLogInfo('*** OCIEXACC: lock Traffic from CPSs to only Agent ports')
        _ibinterfaces = ('stib0','stib1')
        # All possible IB admin IPs
        _cpsiplist = []
        for cps in self.__ocps_json['servers']:
            _cpsiplist += cps['ibAdmin']

        _iptables_cmds = []
        for _if in _ibinterfaces:
            for _cpsip in _cpsiplist: 
                #Forbid every port EXCEPT (!) the ib_domu_ports (7060/7070)
                _iptables_cmds.append(\
                  "-A INPUT -i {} -p tcp -m tcp -m multiport ! --dports {} -s {} -j DROP".format(\
                  _if,','.join(self.__ib_domu_ports),_cpsip))

        if not self.__aMode:
            return _iptables_cmds

        for _domU in self.__domUs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)
            for _iptable_cmd in _iptables_cmds:
                _node.mExecuteCmd('iptables ' + _iptable_cmd)
            #
            # Commit/Save rules for iptables v4
            #
            ebLogInfo('*** Saving iptables rules...')
            _node.mExecuteCmdLog("/sbin/iptables-save > /etc/sysconfig/iptables")
            _node.mExecuteCmdLog("systemctl start iptables")
            _node.mExecuteCmdLog("systemctl enable iptables")
            _node.mDisconnect()

#Main Class
class ExaCCIB_CPS(object):

    def __init__(self, aAllGUIDs, aCheckPkeysRV, aDebug=False, aMode=False):
        self.__allGUIDs = aAllGUIDs
        self.__aMode = aMode
        self.__debug = aDebug
        self.__checkPkeysRv = aCheckPkeysRV
        # Use ATPUtils method to read configuration, need to have a common UTIL class without ATP in name
        self.__remote_cps = ebAtpUtils.mCheckExaboxConfigOption('remote_cps_host')
        _ocps_jsonpath = ebAtpUtils.mCheckExaboxConfigOption('ocps_jsonpath')
        if not _ocps_jsonpath or not os.path.exists(_ocps_jsonpath):
            _msg = 'OCI-Exacc requires ocps_jsonpath setting in exabox configuration for Infiniband Setup'
            raise ExacloudRuntimeError(0x0120, 0xA, _msg)
        with open(_ocps_jsonpath,'r') as fd:
            self.__ocps_json  = json.load(fd)

    def mGetCPSGuids(self):
        _cps_guids     = list(self.__allGUIDs.get('localCPS',[]))
        if self.__remote_cps:
            _cps_guids += self.__allGUIDs.get(self.__remote_cps,[]) 
        return _cps_guids
 

    # Takes the mCheckPkeysConfig return value to have already known values
    def mSetupIBSwitches(self, aDom0s, aCells):

        if not self.__checkPkeysRv:
            _msg = 'Master Switch must be in XML for OCI-ExaCC'
            ebLogError('*** {}'.format(_msg))
            raise ExacloudRuntimeError(0x0120, 0xA, _msg)
        _master, _pname, _skm,  _cps_set = self.__checkPkeysRv
        if _cps_set:
            ebLogInfo('*** CPS GUIDs already present in storage partition')
            return True

        _cmds = []
        _cmds.append('smpartition start')
        if not _pname:
            # Storage partition do not exists, create it with OEDA convention
            _pname = 'st{}'.format(hex(int(_skm,16)|0x8000)[2:])
            _cmds.append('smpartition create -n {} -pkey {} -flag ipoib -m full'.format(\
                         _pname, _skm))

            _lport_fmt = 'smpartition add -n {} -port {{}} -m limited'.format(_pname)
            _fport_fmt = 'smpartition add -n {} -port {{}} -m full'.format(_pname)
            # Add all dom0s ports and all cell ports
            for _dom0 in aDom0s:
                _cmds += list(map(_lport_fmt.format,self.__allGUIDs[_dom0]))
            for _cell in aCells:
                _cmds += list(map(_fport_fmt.format,self.__allGUIDs[_cell]))

        #Add CPS ports on preexisting partition
        _fport_fmt    = 'smpartition add -n {} -port {{}} -m full'.format(_pname)
        _cmds += list(map(_fport_fmt.format,self.mGetCPSGuids()))
        #Commit
        _cmds.append('smpartition commit')

        if not self.__aMode: # Return list of commands in 'test' mode
            return _cmds

        #aMode == True
        _switchNode = exaBoxNode(get_gcontext())
        _switchNode.mConnect(aHost=_master)
        for _cmd in _cmds:
            if self.__debug:
                ebLogDebug('--OCIEXACC IBSetup command: {}'.format(_cmd))
            _switchNode.mExecuteCmd(_cmd)
            _rc = _switchNode.mGetCmdExitStatus()
            if _rc != 0:
                _err = 'Command ({}) failed on IB master, aborting'.format(_cmd)
                ebLogError('*** {}'.format(_err))
                _switchNode.mExecuteCmdLog('smpartition abort')
                raise ExacloudRuntimeError(0x0120, 0xA, _err)
        return True

    def mSetupCPSIB(self):
        _ibnet   = ipaddress.ip_network(self.__ocps_json['ibNetworkCidr'])
        # Since these will be passed to a shell script, escape shell special chars
        _netmask = shlex_quote(str(_ibnet.netmask))
        _pkey    = shlex_quote(self.__ocps_json['pkey'])
        _localhostname = socket.gethostname().split('.')[0]
        _localIPs  = None
        _remoteIPs = None

        for cps in self.__ocps_json['servers']:
            if _localhostname == cps['hostname']:
                _localIPs = self.mQuoteItems(cps['ibAdmin'])
            else:
                _remoteIPs = self.mQuoteItems(cps['ibAdmin'])
        # if _localIPs not found, fallback on first of list
        if not _localIPs:
            _localIPs = self.mQuoteItems(self.__ocps_json['servers'][0]['ibAdmin'])

        ebLogInfo('*** Setting up CPS infiniband with localIPs:{} netmask:{} pkey:{} otherCPSIPs:{}'.format(\
                 _localIPs, _netmask, _pkey, _remoteIPs))

        # Script is a no-op if IPs/PKEY are the same
        _path = os.path.abspath('scripts/network/ociexacc-cps-setupib.sh')
        # Test mode
        if not self.__aMode:
            return (_localIPs,_netmask,_pkey,_remoteIPs,_path)

        try:
            # No need to log, output is kept in exception if error
            subprocess.check_output(['sudo', '/bin/sh',_path,_localIPs[0],_localIPs[1],_netmask,_pkey],
                                                  stderr=subprocess.STDOUT)
            if self.__remote_cps and _remoteIPs:
                _remote_cps = exaBoxNode(get_gcontext())
                _remote_cps.mSetUser('ecra')
                _remote_cps.mConnect(aHost=self.__remote_cps)
                _remote_cmd = 'sudo {} {} {} {} {}'.format(_path, _remoteIPs[0], _remoteIPs[1], _netmask, _pkey)
                _remote_cps.mExecuteCmdLog(_remote_cmd)
                _rc = _remote_cps.mGetCmdExitStatus()
                _remote_cps.mDisconnect()
                if int(_rc) != 0:
                    raise subprocess.CalledProcessError(cmd=_remote_cmd, returncode=int(_rc), output=_remote_cmd)
 
        except subprocess.CalledProcessError as e:
            ebLogError('***ERROR setup script return code({}) with output {}'\
            .format(e.returncode, e.output))
            raise ExacloudRuntimeError(0x0120, 0xA, 'Error while executing {}'.format(_path))

    def mQuoteItems(self, aList):
        return [shlex_quote(item) for item in aList]
