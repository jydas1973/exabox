"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    OVM - Basic functionality

FUNCTION:
    Provide basic/core API for managing OVM Cluster (Cluster Lifecycle,...)

NOTE:
    None

History:
    vikasras    03/17/2021 - Bug 32285465 - BETTER HANDLING OF SSH-KEYGEN
    josedelg    08/03/2021 - Bug 32522779 - Add confirmation when executing
                                            ssh-keygen
    ndesanto    10/02/2019 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01 
    nmallego    11/16/2017 - Bug26830429 - Add class OracleVersion for oracle
                             version to compare and sort
    dekuckre    05/30/2017 - Use debug flag in class:ebCluPreChecks
    dekuckre    05/23/2017 - Bug 25902691: Add mVMPreChecks()
    dekuckre    05/23/2017 - Bug 26035758: Add mCheckDom0Mem()
    mirivier    02/09/2016 - File Creation
"""

from __future__ import print_function

from exabox.core.Error import ebError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug
from exabox.ovm.vmconfig import exaBoxClusterConfig
import os, sys, subprocess, uuid, time, os.path, shlex
from subprocess import Popen, PIPE
import xml.etree.cElementTree as etree
from exabox.core.Context import get_gcontext
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from tempfile import NamedTemporaryFile
from time import sleep
from base64 import b64decode
import hashlib
import re
import json, copy, socket
from exabox.tools.scripts import ebScriptsEngineFetch
from exabox.core.DBStore import ebGetDefaultDB
from multiprocessing import Process, Manager
from exabox.ovm.monitor import ebClusterNode
from exabox.ovm.hypervisorutils import getHVInstance

from exabox.healthcheck.clucheck import ebCluCheck
from exabox.healthcheck.hcconstants import HcConstants,LOG_TYPE, CHK_RESULT


class ebCluPreChecks(ebCluCheck):

    def __init__(self, aCluCtrlObj, aCluHealthObj=None):
        super(ebCluPreChecks, self).__init__(aCluCtrlObj, aCluHealthObj)

        self.__cluctrl = aCluCtrlObj
        self.__verbose = False
        self.__cluster_host_d = {}

    def __del__(self):
        #
        super(ebCluPreChecks, self).__del__()
        #ebLogInfo(" ebCluPreChecks destr called")
        print(" ebCluPreChecks dest called for ", self)
    
    def mNetworkDom0PreChecks(self):

        def _dom0_network_validation(_dom0):

            _rc = False
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            #
            # Check critical configuration files
            #
            if not _node.mFileExists('/opt/oracle.cellos/cell.conf'):
                ebLogError('ebPC Dom0 Network critical error. cell.conf not found in /opt/oracle.cellos')
                return _rc
            #
            # Main network validation on Dom0
            #
            _fin, _fout, _ferr = _node.mExecuteCmd('/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime', aTimeout=180)
            _out = _fout.readlines()
            if _out:
                _rc = False
                for _line in _out:
                    if _line.find('Consistency check PASSED'):
                        ebLogDebug('Network Consistency checks PASSED on {0}'.format(_dom0))
                        _rc = True
                        break

                if not _rc:
                    for _line in _out:
                        ebLogError(_line)

            _node.mDisconnect()

            return _rc
        #
        # Sequential Dom0 pre-checks - TODO: Add parallel pre-checks
        #
        _rc_d = {}
        for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair():
                _rc =_dom0_network_validation(_dom0)
                _rc_d[_dom0] = _rc

        if False in _rc_d.values():
            return False
        else:
            return True

    def mNetworkBasicChecks(self,aVerbose=False):

        _network_ip_list = {}
        _machinesConfigDict = self.__cluctrl.mGetMachines().mGetMachineConfigList()
        for _machine in _machinesConfigDict.keys():
            _machineConfig = _machinesConfigDict[_machine]
            _hostname = _machineConfig.mGetMacHostName()
            _networks = _machineConfig.mGetMacNetworks()
            if aVerbose:
                ebLogInfo('*** Hostname: %s' % (_hostname))
            for _network in _networks:
                _ip = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_network).mGetNetIpAddr()
                if aVerbose:
                    ebLogInfo('    _network: %s %s' % (_network,_ip))
                if _ip not in _network_ip_list.keys():
                    _network_ip_list[_ip] = _network
                else:
                    ebLogError('*** duplicate IP detected ***: %s clashes with: %s / %s' % (_network,_ip,_network_ip_list[_ip]))

    def mConnectivityChecks(self,aCheckDomU=True,aCheckMode=None):

        _rc = False

        _dom0s, _domUs, _cells, _switches = self.__cluctrl.mReturnAllClusterHosts()
        _cluhosts = _dom0s + _domUs + _cells + _switches

        _cluster_host_d = {}
        #
        # Collect info on all hosts
        #
        for _host in _cluhosts:
            _neto = self.__cluctrl.mGetNetworks().mGetNetworkConfigByName(_host)
            _clunode = ebClusterNode()
            _cluster_host_d[_host] = _clunode
            _clunode.mSetClusterId(self.__cluctrl.mGetKey())
            _clunode.mSetHostname(_host)
            _clunode.mSetNetworkIp(_neto.mGetNetIpAddr())
            if _host in _dom0s:
                _clunode.mSetNodeType('dom0')
            elif _host in _domUs:
                _clunode.mSetNodeType('domu')
            elif _host in _cells:
                _clunode.mSetNodeType('cell')
            elif _host in _switches:
                _clunode.mSetNodeType('switch')
        #
        # Check HOST connectivity
        #
        for _host in _cluster_host_d.keys():

            _clunode = _cluster_host_d[_host]
            #
            # Check if HOST is pingable
            #
            if not self.__cluctrl.mPingHost(_host):
                _clunode.mSetPingable(False)
                _clunode.mSetSSHConnection(None)
                _clunode.mSetRootSSHDMode(None)
                _clunode.mSetPwdAuthentication(None)
                _clunode.mSetWeakPassword(None)
            else:
                _clunode.mSetPingable(True)
            #
            # Check if SSH connectivity
            #
            if _clunode.mGetPingable():

                _node = exaBoxNode(get_gcontext())
                try:
                    _node.mConnect(aHost=_host)
                except:
                    _clunode.mSetSSHConnection(False)
                    continue
                _clunode.mSetSSHConnection(True)
                #
                # Node specific checks/info
                #
                if _clunode.mGetNodeType() == 'switch':
                    _cmd4_str = 'smpartition list active no-page | head -10'
                    _i, _o, _e = _node.mExecuteCmd(_cmd4_str, aTimeout=180)
                    _out = _o.readlines()
                    if _out:
                        for _line in _out:
                            if _line.find('Default=') != -1:
                                _default = _line[len('Default='):-2]
                                _clunode.mSetSwitchDefault(_default)
                            elif _line.find('ALL_CAS=') != -1:
                                _all_cas = _line[len('ALL_CAS='):-2]
                                _clunode.mSetSwitchAllCas(_all_cas)

                _node.mDisconnect()
            #
            # Short report
            #
            if _clunode.mGetSSHConnection():
                ebLogDebug('Connectivity check to {1} host: {0} PASS'.format(_host,_clunode.mGetNodeType()))
                _rc = True
            elif _clunode.mGetNodeType() == 'domu' and aCheckDomU is False:
                _rc = True
                ebLogWarn('Connectivity check to domu: {0} FAILED (non critical)'.format(_host))
            elif _clunode.mGetPingable():
                ebLogError('Connectivity check to {1} host: {0} FAILED (ping: OK ssh: FAIL)'.format(_host, _clunode.mGetNodeType()))
                _rc = False
            else:
                ebLogError('Connectivity check to {1} host: {0} FAILED'.format(_host,_clunode.mGetNodeType()))
                _rc = False

        self.__cluster_host_d = _cluster_host_d

        return _rc

    def mResetNetwork(self,aCheckMode=None):

        for _dom0, _  in self.__cluctrl.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)

            # Reset interface to
            _cmd  = 'ifconfig ib0 0.0.0.0 ; ifconfig ib1 0.0.0.0 ; ifconfig vmbondeth0 0.0.0.0 ; ifconfig vmbondeth1 0.0.0.0'
            _cmd += ' ; ifconfig eth1 0.0.0.0 ; ifconfig eth2 0.0.0.0 ; ifconfig eth3 0.0.0.0 ; ifconfig eth4 0.0.0.0 ; ifconfig eth5 0.0.0.0'
            _node.mExecuteCmdLog(_cmd, aTimeout=180)

            _node.mDisconnect()

        return True

    def mVMPreChecks(self, aHost=None):

        #
        # Checks if VM/s already exist/s
        #
        _exists = False
        _node = exaBoxNode(get_gcontext())
        for _dom0, _domU in self.__cluctrl.mReturnDom0DomUPair():
            # if aHost is provided then do pre-checks for only that aHost(dom0)
            # otherwise do pre-checks for all the dom0's.
            if ((aHost and _dom0 == aHost) or not aHost):
                _node.mConnect(aHost=_dom0)
                _vm_image='/EXAVMIMAGES/GuestImages/%s/vm.cfg' % (_domU)
                _rc = _node.mFileExists(_vm_image)
                if _rc:
                    ebLogWarn('*** VM %s already exists' % (_domU))
                    _exists = True
                else:
                    if self.__cluctrl.mIsDebug():
                        ebLogInfo('*** VM %s is not present' % (_domU))
                _node.mDisconnect()

        return _exists

    # Dom0 test:
    # Check for available free memory in dom0.
    # The memsize in XML should not be greater than the avaiable free memory
    # in dom0 during pre-provisioning.

    def mCheckDom0Mem(self, aHost):

        from exabox.ovm.clucontrol import ebCluVMSizesConfig
        _host = aHost
        _ebox = self.__cluctrl

        _dom0List = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]
        if _host not in _dom0List:
            ebLogError('ERROR: Node type for which available free memory is checked is not dom0.')
            return False

        _vmszconfig = ebCluVMSizesConfig(_ebox._exaBoxCluCtrl__config)
        # Find the memsize recorded in XML.
        _memXML = _vmszconfig.mGetVMSize('Large').mGetVMSizeAttr('MemSize')

        _vm = getHVInstance(_host)
        _freememint = _vm.getDom0FreeMem()
        if _memXML > (_freememint / 1024):
            ebLogWarn('memsize in XML is greater than available free memory in dom0 - %s' %(_host))
            return False
        return True

    # end

    # Check for available free space on given parition.
    #return True: if used space less than threshold value
    def mCheckUsedSpace(self, aHost, aPartition, aThreshold):

        _host       = aHost
        _partition  = aPartition 
        _threshold  = aThreshold
        _ebox       = self.__cluctrl
        #
        _cmdstr = 'df -P ' + _partition + ' | tail -1 | awk \'0+$5 >= ' + _threshold + ' {print}\''
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_host)
        _, _o, _ = _node.mExecuteCmd(_cmdstr, aTimeout=180)
        _out = _o.readlines()
        _node.mDisconnect()
        if len(_out):
            ebLogDebug('%s partition space used more than threshold value for host - %s' %(_partition,_host))
            return False
        return True
    # end


#class added for ssh setup
class ebCluSshSetup(object):
    
    def __init__(self, aCluCtrlObj):

        self.__cluctrl = aCluCtrlObj
        self.__verbose = False

    # Functions that handle ssh passwordless connetion between hosts.

    def mGetSSHPublicKeyFromHost(self, aHost):
        """
        Returns aHost's public ssh key value. If the key doesn't exist, then it is created with ssh-keygen command.
        """
        _ssh_key = ''
        _cmd = "if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1"\
               " -name 'id_rsa.pub'` ]]; then ssh-keygen -q -t rsa -N \"\" -f "\
               "~/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; "\
               "cat ~/.ssh/id_rsa.pub"
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aHost)
        _in, _out, _err = _node.mExecuteCmd(_cmd, aTimeout=180)
        if _node.mGetCmdExitStatus():
            ebLogError('Failed to get public key for host %s: mExecuteCmd Failed: with error: %s' % (aHost, _err.readlines()))
        else:    
            _output = _out.readlines()
            if _output:
                _ssh_key  = _output[0].encode('utf-8').strip()
                ebLogInfo("Obtained SSH public key for host %s" % aHost)
        _node.mDisconnect()
        return _ssh_key

    def mAddKeyToHosts(self, aHostKey, aRemoteHostList):
        """
        Adds the ssh public key (aHostKey) to the nodes listed in aRemoteHostList.
        """
        if not aHostKey:
            ebLogError("Host's SSH public key not found. Nothing to do.")
            return -1

        _cmd = 'echo %s >> ~/.ssh/authorized_keys' % (aHostKey)
        for _h in aRemoteHostList:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_h)
            _node.mExecuteCmdLog(_cmd, aTimeout=180)
            _node.mDisconnect()

    def mRemoveKeyFromHosts(self, aHostKey, aRemoteHostList):
        """
        Removes all aHost's ssh public keys found in the authorized_keys file on each node listed in aRemoteHostList.
        """
        #remove entry using public key
        _cmd = "ex '+g/.*{0}.*/d' -scwq ~/.ssh/authorized_keys".format(aHostKey)
        for _h in aRemoteHostList:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_h)
            _node.mExecuteCmdLog(_cmd, aTimeout=180)
            _node.mDisconnect()

    def mAddToKnownHosts(self, aHost, aRemoteHostList):
        """
        Adds all nodes listed in aRemoteHostList to the known_hosts file in aHost.
        """
        _cmd = 'ssh-keyscan -t rsa %s >> ~/.ssh/known_hosts;'
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aHost)
        for _h in aRemoteHostList:
            _node.mExecuteCmdLog(_cmd % _h, aTimeout=180)
        _node.mDisconnect()

    def mRemoveFromKnownHosts(self, aHost, aRemoteHostList):
        """
        Removes all nodes listed in aRemoteHostList from the known_hosts file in aHost.
        """
        _cmd = 'ssh-keygen -R %s'
        _node = exaBoxNode(get_gcontext()) 
        _node.mConnect(aHost=aHost)
        for _h in aRemoteHostList:
            _node.mExecuteCmdLog(_cmd % _h, aTimeout=180)
        _node.mDisconnect()

    def mSetSSHPasswordless(self, aHost, aRemoteHostList):
        """
        Set ssh passwordless between the host and a list of remote hosts.
        """
        #Get ssh public key from the host
        _key = self.mGetSSHPublicKeyFromHost(aHost)
        
        ##### TBD: check if all cells are healthy/pingable first
        # Add cells to known_hosts in host
        self.mRemoveFromKnownHosts(aHost, aRemoteHostList)
        self.mAddToKnownHosts(aHost, aRemoteHostList)
        # Add host's ssh public key to the cells
        self.mRemoveKeyFromHosts(aHost, aRemoteHostList)
        self.mAddKeyToHosts(_key, aRemoteHostList)
        return _key

    def mCleanSSHPasswordless(self, aHost, aRemoteHostList):
        """
        Cleans the ssh passwordless configuration.
        """
        self.mRemoveFromKnownHosts(aHost, aRemoteHostList)
        self.mRemoveKeyFromHosts(aHost, aRemoteHostList)

###############################################################################

class OracleVersion(object):
    """
    Handle operations on oracle version like compare, sort and
    get latest/highest oracle versions.
    """

    def mCompareVersions(self, aCurrentVersion = None, aTargetVersion = None):
        """
        Compare current and target version and return based on the comparison.
        Return 0, if aCurrentVersion and aTargetVersion are equal,
        return -1, if aCurrentVersion is lesser than aTargetVersion,
        return 1, if aCurrentVersion is greater than aTargetVersion. 
        This function is expected to work for oracle version format and
        also for any two given strings.

        """
        if not aCurrentVersion or not aTargetVersion:
            ebLogError ("Invalid inputs: Provide valid compare versions")
            return None

        # if the given input versions are numbers, do the number camparision
        if type(aCurrentVersion) == int and type(aTargetVersion) == int:
            if aCurrentVersion == aTargetVersion:
                return 0
            elif aCurrentVersion > aTargetVersion:
                return 1
            else:
                return -1

        _ver1, _ver2 = aCurrentVersion, aTargetVersion
        try:
            # IBSWITCH version can have fomrat like 2.1.8-1 and needs to be 
            # taken care 
            _ver1 = (re.sub('[-]', '.', _ver1))
            _ver2 = (re.sub('[-]', '.', _ver2))

            _ver1 = _ver1.split(".")
            _ver2 = _ver2.split(".")

            _comp_count_to_cmp = min(len(_ver1), len(_ver2))

            for i in range (_comp_count_to_cmp):
                # Do the numeric comparison
                if _ver1[i].isdigit() and _ver2[i].isdigit():
                     if int(_ver1[i]) == int(_ver2[i]):
                        continue
                     elif int(_ver1[i]) > int(_ver2[i]):
                        return 1
                     else:
                        return -1
                # Do the alphanumeric comparison
                elif _ver1[i].isalnum() or _ver2[i].isalnum():
                     if _ver1[i] == _ver2[i]:
                        continue
                     elif _ver1[i] > _ver2[i]:
                        return 1
                     else:
                        return -1

            if ((i + 1) == _comp_count_to_cmp):
                if (len(_ver1) == len(_ver2)):
                    return 0
                elif (len(_ver1) > len(_ver2)):
                    return 1
                else:
                    return -1
        except Exception as err:
            ebLogWarn("Version error: " + str(err))
            return None

    def mSortVersion(self, aListVersions):
        """
        Sort the exadata oracle version in ascending order.
        """
        # if no elements in the list, just return 
        if not aListVersions or len(aListVersions) == 0:
            return None
        # if only one element in the list, nothing to be sort.
        elif len(aListVersions) == 1:
            return aListVersions

        _sortlist = sorted(aListVersions, cmp=self.mCompareVersions)
        return _sortlist        

    def mGetHighestVer(self, aListVersions):
        """
        This function sort and get the highest version from the given list
        """
        # if no elements in the list, just return 
        if not aListVersions or len(aListVersions) == 0:
            return None
        # if only one element in the list, nothing to be compare, return as is.
        elif len(aListVersions) == 1:
            return aListVersions[0]

        _sortlist = sorted(aListVersions, cmp=self.mCompareVersions)
        return _sortlist[-1]

