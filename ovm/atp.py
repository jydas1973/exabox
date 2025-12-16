import abc, os, json, re
from tempfile import NamedTemporaryFile
from typing import Dict, Set, Tuple
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.utils.node import connect_to_host

DB_ROUTE_PATH='/var/opt/oracle/misc/db-route'
AUTONOMOUS_FLAG='AutonomousDb'
ATP_OPTIONS_KEYS = ["backup_network", "client_network", "second_listener_port", "client_vip"]
ATP_OPTIONS_FROM_PAYLOAD_KEYS = ["casperIp", "omvcnSubnet"]

#
# ATP Config
#
"""
### Default apt setting in exabox.conf
"atp": {
        "dom0_iptables": "True",
        "backup_ssh" : "True",
        "dnsmasq" : "True",
        "domU_route" : "True",
        "add_backup_listener" : "True",
        "add_scanname_etc_hosts" : "True",
        "enable_namespace" : "True",
    }
"""

"""
Mapping between all string representation of all subtypes of ebAtpStep
and a pair of sets of ATP settings from exabox.conf.
The first element of the pair represents all of the settings that must be
enabled and the second one, all of the settings that must be disabled to
to be able to run mExecute from that class.

For example:
In order to execute AtpSetupASMListener, we need that both
add_asm_listener & add_backup_listener options from the atp section of
exabox.conf to be True.
"""
ATP_FEATUREKEY_CLASSNAME_MAP: Dict[str, Tuple[Set[str], Set[str]]]={
    "AtpAddRoutes2DomU" :       ({ "domU_route" },                              {}),
    "AtpAddiptables2Dom0" :     ({ "dom0_iptables" },                           {}),
    "AtpSetupSecondListener" :  ({ "add_backup_listener" },                     {}),
    "AtpCreateAtpIni" :         ({ "create_atp_ini" },                          {}),
    "AtpAddScanname2EtcHosts":  ({ "add_scanname_etc_hosts" },                  {}),
    "AtpSetupNamespace":        ({ "enable_namespace" },                        {}),
    "AtpSetupASMListener":      ({ "add_asm_listener", "add_backup_listener" }, {})
}

def areATPFeatureDependenciesSatisfied(aClassName: str, aFeatureDependenciesDict: Dict[str, Tuple[Set[str], Set[str]]]) -> bool:
    """
    Check if all of the specified ATP configuration dependencies are satisfied
    in order to be able to execute an ATP step.

    See ATP_FEATUREKEY_CLASSNAME_MAP to know how dependencies work.
    """
    _enabledFeatures, _disabledFeatures = aFeatureDependenciesDict[aClassName]
    return all(map(ebAtpUtils.isFeatureEnabled, _enabledFeatures)) and \
        not any(map(ebAtpUtils.isFeatureEnabled, _disabledFeatures))

class ebCluATPConfig(object):
    """
        ebCluATPConfig is the class that captures all ATP related json payload settings
        and ATP related parameters such as backup IF IPs, domain, management network info, etc
    """
    def __init__(self, aOptions, aDebug=False):

        self.__isATP = False
        self.__ATPOptions = None
        self.__debug = aDebug

        # ATP setting in JSON
        if aOptions is None:
            ebLogWarn("*** ATP aOptions is None")
            self.__jconf = None
        else:
            self.__jconf = aOptions.jsonconf
        if self.__jconf is not None:
            _jconf_keys = list(self.__jconf.keys())
            if _jconf_keys is not None:
                if 'atp' in _jconf_keys:
                    self.__ATPOptions = self.__jconf['atp']
                    if AUTONOMOUS_FLAG in list(self.__ATPOptions.keys()):
                        if self.__ATPOptions[AUTONOMOUS_FLAG].lower().strip() == 'y':
                            self.__isATP = True
                        ebLogInfo('*** ATP JSON payload with {1} value {0} specified'.format(self.__isATP, AUTONOMOUS_FLAG))
                    else:
                        ebLogInfo('*** ATP JSON payload with no value of {0} specified'.format(AUTONOMOUS_FLAG))
            if self.__isATP:
                        for key in ATP_OPTIONS_FROM_PAYLOAD_KEYS:
                            _option_value = self._getJsonValueByKey(key)
                            if _option_value != None:
                                self.__ATPOptions[key] = _option_value
        
        if self.__debug:
            ebLogDebug(self.__ATPOptions)

    def __repr__(self):
        _rtn_str = """
        __IsATP: {isATP}
        """.format(isATP=self.__isATP)
        if self.__ATPOptions:
            for key in list(self.__ATPOptions.keys()):
                _rtn_str += "%s: %s" % (key, self.__ATPOptions[key])
        return _rtn_str

    def _getJsonValueByKey(self, keyStr):
        if self.__jconf is not None:
            _jconf_keys = list(self.__jconf.keys())
            if _jconf_keys is not None:
                if keyStr in self.__jconf['atp']:
                    ebLogDebug('*** ATP JSON payload contains value for {0} specified {1}'.format(keyStr, self.__jconf['atp'][keyStr]))
                    return self.__jconf['atp'][keyStr]
                else:
                    ebLogWarn('*** ATP JSON payload with no value of {0} specified'.format(keyStr))

    ## ATP specific parameters
    ## aOMVNCSubnet, aCasperSubnet, aCCDBSubnet, aORDSSubnet, aBackupNicIP, aBackupNic
    ##  Hard coding for some values now until I know where to find the values in the payload

    def isATP(self):
        return self.__isATP

    def mGetATPOptions(self):
        if self.__isATP:
            return self.__ATPOptions
        return None

    def mGetBackupIP(self, aDomU, aMachines, aNetworks):
        _domU_mac = aMachines.mGetMachineConfig(aDomU)
        _net_list = _domU_mac.mGetMacNetworks()
        _netConfig = ebATPNetworkUtils.mATPGetBackupNetworkConfig(_net_list, aNetworks)
        return _netConfig.mGetNetIpAddr()

    def mGetClientIP(self, aDomU, aMachines, aNetworks):
        _domU_mac = aMachines.mGetMachineConfig(aDomU)
        _net_list = _domU_mac.mGetMacNetworks()
        _netConfig = ebATPNetworkUtils.mATPGetClientNetworkConfig(_net_list, aNetworks)
        return _netConfig.mGetNetIpAddr()


    def mGetATPOption(self, aKeyword):
        """
        :param aKeyword: ATP Option/param keyword
        :return: value from payload or exabox.conf or None.
        """
        _rtn_val = None
        if self.__ATPOptions != None:
            if aKeyword in list(self.__ATPOptions.keys()):
                _rtn_val = self.__ATPOptions[aKeyword]
        else:
            _atp_defaults = ebAtpUtils.mCheckExaboxConfigOption('atp')
            _default_value = _atp_defaults[aKeyword]
            if _default_value != None:
                return _default_value
        return _rtn_val

    def mGetBackupNIC(self, aDomU, aMachines, aNetworks):
        """
        :param aDomU: DomU
        :return: Backup IF dev name
        """
        _domU_mac = aMachines.mGetMachineConfig(aDomU)
        _net_list = _domU_mac.mGetMacNetworks()
        _netConfig = ebATPNetworkUtils.mATPGetBackupNetworkConfig(_net_list, aNetworks)
        return _netConfig.mGetNetMaster()

    def mGetClientNIC(self, aDomU, aMachines, aNetworks):
        """
        :param aDomU: DomU
        :return: Client IF dev name
        """
        _domU_mac = aMachines.mGetMachineConfig(aDomU)
        _net_list = _domU_mac.mGetMacNetworks()
        _netConfig = ebATPNetworkUtils.mATPGetClientNetworkConfig(_net_list, aNetworks)
        return _netConfig.mGetNetMaster()

"""
   Base class for ATP related steps
"""
class ebAtpStep(metaclass=abc.ABCMeta):

    def __init__(self, aNode, aAtp):
        super(ebAtpStep, self).__init__()
        self._node = aNode
        self._atp = aAtp
        self._stepname = self.__class__.__name__



    @abc.abstractmethod
    def _mExecute(self):
        raise NotImplementedError

    def mExecute(self):
        if areATPFeatureDependenciesSatisfied(self._stepname, ATP_FEATUREKEY_CLASSNAME_MAP):
            self.mLogInfo("Executing %s" % self._stepname)
            self._mExecute()

    def mGetStepName(self):
        return self._stepname

    def mLogInfo(self, msg):
        ebLogInfo("*** ATP %s" % msg)

    def mLogDebug(self, msg):
        ebLogDebug("*** ATP %s" % msg)

    def mLogError(self, msg):
        ebLogError("*** ATP %s" % msg)

    def mLogWarn(self, msg):
        ebLogWarn("*** ATP %s" % msg)

class AtpAddRoutes2DomU(ebAtpStep):
    ### if aSubnets is set, we only add the subnets instead of getting data from atp properties
    def __init__(self, aNode, aAtp, aDomU, aPair, aMachines, aNetworks, aSubnets=None):
        ebAtpStep.__init__(self, aNode, aAtp)
        self.__domu = aDomU
        self.__pair = aPair
        self.__machines = aMachines
        self.__networks = aNetworks
        self.__subnets = aSubnets


    def _mAddRoute2Backup(self, aNetwork, aNetmask):
        _route_bin = DB_ROUTE_PATH
        _dev = self._atp.mGetBackupNIC(self.__domu, self.__machines, self.__networks).strip()
        _gateway = ebAtpUtils.mGetIFGateway(self.__pair, self.__machines, self.__networks, 'backup', self.__domu)
        _cmd = "%s add -net %s gw %s netmask %s dev %s" % (_route_bin, aNetwork, _gateway, aNetmask, _dev)
        self.mLogInfo("Running: " + _cmd + " on: " + self.__domu)
        (_, _o, _e) = self._node.mExecuteCmd(_cmd)
        if self._node.mGetCmdExitStatus():  ## need to improve error handling
            raise ExacloudRuntimeError(0x0651, 0x0A, "%s error. e:%s  o:%s" % (
                _cmd, _e.readlines(), _o.readlines()))

    def _mExecute(self):
        #_mgmt_subnets = self.__subnets
        #if self.__subnets is not None:
        self.mLogInfo("Adding ATP routes")
        _casperData = self._atp.mGetATPOption('casperIp').strip()
        if _casperData is not None:
            self.mLogInfo("Adding route for Casper") 
            if ebAtpUtils.isCidr(_casperData):
                _casperIP, _netmask = ebAtpUtils.cidr_to_netmask(_casperData)
            else:
                _casperIP = _casperData
                _netmask = "255.255.255.255"
            self._mAddRoute2Backup(_casperIP, _netmask)
        else:
            self.mLogWarn("No Casper subnet defined")
 
        _mgmtSubnets = self._atp.mGetATPOption('reserved_subnets')
        if _mgmtSubnets is not None:
            self.mLogInfo("Adding DG or generic routes")
            for _subnet in _mgmtSubnets:
                if ebAtpUtils.isCidr(_subnet):
                    _network, _netmask = ebAtpUtils.cidr_to_netmask(_subnet)
                    self._mAddRoute2Backup(_network, _netmask)
        else:
            self.mLogWarn("No reserved subnets defined")

"""
   Desc:  Add iptables to dom0 to limit traffic for domU
          _node should be the dom0
   Input:
"""
class AtpAddiptables2Dom0(ebAtpStep):

    def __init__(self, aNode, aAtp, aPair, aMachines, aNetworks):
        ebAtpStep.__init__(self, aNode, aAtp)
        self.__pair = aPair
        self.__machines = aMachines
        self.__networks = aNetworks

    def _mExecute(self):
        # Create /opt/exacloud/network/vif-all-client-ips

        _filename = ebAtpUtils.DOM0_VIF_INFO_FILE
        _myClientIPs = ebAtpUtils.mGetIF2IPMapping(self.__pair, self.__machines, self.__networks)['client']

        self.mLogInfo("Creating %s" % _filename)
        _str_config = "### Created for ATP deployments by atp.py\n"
        for _domU in list(_myClientIPs.keys()):
            _str_config += ("%s %s %s %s\n" %(_myClientIPs[_domU], _domU, ebAtpUtils.mGetClientMac(self.__pair, self.__machines, self.__networks, _domU), ebAtpUtils.mGetIFGateway(self.__pair, self.__machines, self.__networks, "backup", _domU)))
        _str_config += ("whitelist:tcp=%s" % ','.join(map(str,ebAtpUtils.mGetDictFromGen2Payload(self._atp.mGetATPOption('whitelist'), "client/protocol/tcp"))))
        _clientIpstemp = NamedTemporaryFile(delete=False)
        self.mLogInfo(_str_config)
        _clientIpstemp.file.write(_str_config.encode('utf8'))
        _clientIpstemp.file.close()

        ## The file will be used by /etc/xen/scripts/vif-bridge
        for _dom0, _domU in self.__pair:
            _myfilename = _filename + "." + _domU
            self.mLogInfo('*** Saving Cluster configuration on dom0: '+_dom0+' in '+ _myfilename)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            self.mLogInfo("Removing %s on %s" % ( _myfilename, _dom0 ))
            _node.mExecuteCmd('mkdir -p %s' % ebAtpUtils.DOM0_EXACLOUD_CONFIG_NETWORK_DIR)
            _node.mCopyFile(_clientIpstemp.name, _myfilename)
            _node.mDisconnect()
            # Cleanup (remove temporary file)
        os.unlink(_clientIpstemp.name)
        assert (os.path.exists(_clientIpstemp.name) == False)


class AtpAddScanname2EtcHosts(ebAtpStep):
    def __init__(self, aNode, aAtp, aDomU):
        ebAtpStep.__init__(self, aNode, aAtp)
        self.__domU = aDomU

    def _mExecute(self):
        self.mLogInfo(" Adding scan to /etc/hosts on %s. " % self.__domU)
        _net = ebAtpUtils.mReadAtpIniFile2Dict(self.__domU)
        _scanip = _net['scanip']
        _scanname = _net['scanname']
        if not '.' in _scanname:
            _fqdnname = '.'.join([_scanname,_net['domainname']])
        else:
            _fqdnname = _scanname
            _scanname = _fqdnname.split('.',1)[0]

        _cmd="""[ "`grep -e '^{scanip}\s' /etc/hosts |wc -l `" -eq 0 ] && echo {scanip} {fqdnname} {scanname} '### Added by ATP' >> /etc/hosts"""\
             .format(scanip=_scanip.replace('.','\.'), fqdnname=_fqdnname,\
                     scanname=_scanname)
        _nodeDomU = exaBoxNode(get_gcontext())
        self.mLogInfo(" Running %s. " % _cmd)
        _nodeDomU.mConnect(aHost=self.__domU)
        _nodeDomU.mExecuteCmd(_cmd)
        _nodeDomU.mDisconnect()

class AtpSetupSecondListener(ebAtpStep):

    def __init__(self, aNode, aAtp, aPair, aMachines, aNetworks, aDbName, aClusters, aOptions):
        ebAtpStep.__init__(self, aNode, aAtp)
        self.__pair = aPair
        self.__dbname = aDbName
        self.__machines = aMachines
        self.__networks = aNetworks
        self.__clusters = aClusters
        self.__options = aOptions

    def _mExecute(self):

        if self.__dbname is None:
            self.mLogInfo("DB Name is None, perform no action.")
            #return

        self.mLogInfo("Creating second listener")

        self.mLogInfo(self.__pair)
        _secListenerPort = ebAtpUtils.mGetExaboxATPOption("sec_listener_port")
        ## Run as root only on one of the domU nodes:
        _backupVips = []
        for _dom0, _domU in self.__pair:
            _backupVips.append((_domU.split('.')[0], ebAtpUtils.mGetBackupVipFromAtpIni(_domU)))
        _dom0, _domU = self.__pair[0]
        _oracle_home = ebAtpUtils.mGetOracleHome(_domU, self.__dbname)
        _grid_home = ebAtpUtils.mGetOracleHome(_domU, 'grid')
        _srvctl_bin = '{grid_home}/bin/srvctl'.format(grid_home=_grid_home)
        _cmd_str = "echo $((`{srvctl_bin} config network |grep exists |wc -l` + 1))".format(srvctl_bin=_srvctl_bin)
        _nodeDomU = exaBoxNode(get_gcontext())
        _nodeDomU.mConnect(aHost=_domU)
        _, _out, _ = _nodeDomU.mExecuteCmd(_cmd_str)
        _out = _out.readlines()
        _nodeDomU.mDisconnect()
        ## assume 1 is for client nic
        _netnum='2'
        if (_out is not None and len(_out) != 0):
            _netnum = _out[0].strip()
            ebLogInfo("netnum from cmd: " + _netnum)
        _mynum = ebAtpUtils.mGetExaboxATPOption("netnum")
        if _mynum:
            _netnum = _mynum
            self.mLogInfo("netnum from exabox.conf: " + _netnum)

        _backupIp = ebAtpUtils.mGetBackupIps(self.__pair, self.__machines, self.__networks, aWanted=_domU)
        _backupNetmask = ebAtpUtils.mGetIFNetmask(self.__pair, self.__machines, self.__networks, 'backup', _domU)
        _backupSubnet = ebAtpUtils.mGetSubnetFromIpAndNetmask(_backupIp, _backupNetmask)
        _backupScanName = ebAtpUtils.mGetBackupScannameFromAtpIni(_domU)
        _cmd_run_as_root = """
        {grid_home}/bin/srvctl add network -netnum {netnum} -subnet {subnet}/{netmask}/bondeth1
        {grid_home}/bin/crsctl start res ora.net2.network -unsupported
        {grid_home}/bin/srvctl add vip -node {domU1} -netnum {netnum} -address {backupVip1}/{backupNetmask}
        {grid_home}/bin/srvctl add vip -node {domU2} -netnum {netnum} -address {backupVip2}/{backupNetmask}
        {grid_home}/bin/srvctl start vip -netnum {netnum} -node {domU1}
        {grid_home}/bin/srvctl start vip -netnum {netnum} -node {domU2}
        {grid_home}/bin/srvctl add scan -scanname {backupScanname} -netnum 2
        """.format(grid_home=_grid_home, subnet=_backupSubnet, netmask=_backupNetmask, domU1=_backupVips[0][0], domU2=_backupVips[1][0],
                   backupVip1=_backupVips[0][1], backupVip2=_backupVips[1][1], backupNetmask=_backupNetmask, netnum=_netnum, backupScanname=_backupScanName)
        _nodeDomU = exaBoxNode(get_gcontext())
        _nodeDomU.mConnect(aHost=_domU)
        self.mLogInfo(_cmd_run_as_root)
        _output = _nodeDomU.mExecuteScript(_cmd_run_as_root)
        _nodeDomU.mDisconnect()
        self.mLogInfo(_output)

        ## Run as grid user on one node

        _backupIp = ebAtpUtils.mGetBackupIps(self.__pair, self.__machines, self.__networks, aWanted=_domU)
        _backupNetmask = ebAtpUtils.mGetIFNetmask(self.__pair, self.__machines, self.__networks, 'backup', _domU)
        _backupSubnet = ebAtpUtils.mGetSubnetFromIpAndNetmask(_backupIp, _backupNetmask)
        _cmd_run_as_grid="""
{grid_home}/bin/srvctl add listener -listener LISTENER_BKUP -netnum {netnum} -endpoints TCP:{secListenerPort} -oraclehome {gridHome}
{grid_home}/bin/srvctl add scan_listener -listener LISTENER_BKUP -netnum {netnum} -endpoints TCP:{secListenerPort}
{grid_home}/bin/srvctl start listener -listener LISTENER_BKUP
{grid_home}/bin/srvctl start scan_listener -netnum {netnum} 
{grid_home}/bin/srvctl config scan_listener -netnum {netnum} 
""".format(grid_home=_grid_home, secListenerPort=_secListenerPort, gridHome=_grid_home, netnum=_netnum)
        _nodeDomU = exaBoxNode(get_gcontext())
        _nodeDomU.mSetUser('grid')
        _nodeDomU.mConnect(aHost=_domU)
        self.mLogInfo(_cmd_run_as_grid)
        _output = _nodeDomU.mExecuteScript(_cmd_run_as_grid)
        _nodeDomU.mDisconnect()
        self.mLogInfo(_output)
        #Run as oracle user on all nodes
        if _oracle_home is not None:
            for _dom0, _domU in self.__pair:
                _oracle_sid = ebAtpUtils.mGetOracleSid(_domU, self.__dbname)
                _clientVip = ebAtpUtils.mGetClientVip(self.__clusters, self.__machines, _domU)
                _backupVip = ebAtpUtils.mGetBackupVipFromAtpIni(_domU)
                _cmd_run_as_oracle="""
export ORACLE_HOME={oracleHome} 
export ORACLE_SID={oracleSid}
$ORACLE_HOME/bin/sqlplus /nolog <<EOF
connect / as sysdba
alter system set LOCAL_LISTENER='(ADDRESS_LIST=
(ADDRESS=(PROTOCOL=TCP)(HOST={clientVip})(PORT=1521))
(ADDRESS=(PROTOCOL=TCP)(HOST={backupVip})(port={secListenerPort})))';
EOF
""".format(oracleHome=_oracle_home, clientVip=_clientVip, backupVip=_backupVip, secListenerPort=_secListenerPort, dbname=self.__dbname, oracleSid=_oracle_sid)
                _nodeDomU = exaBoxNode(get_gcontext())
                _nodeDomU.mConnect(aHost=_domU)
                _nodeDomU.mSetUser('oracle')
                self.mLogInfo(_cmd_run_as_oracle)
                _nodeDomU.mExecuteScript(_cmd_run_as_oracle)
                _nodeDomU.mDisconnect()
        else:
            self.mLogInfo("Skipped registering db to listener. ORACLE_HOME is None")

class AtpCreateAtpIni(ebAtpStep):
    """Call this at the end of the create service to inject ATP ini to domU"""
    def __init__(self, aNode, aAtp, aCustomerNetwork, aDomU):
        ebAtpStep.__init__(self, aNode, aAtp)
        self.__customerNetwork = aCustomerNetwork
        self.__domu = aDomU

    def _mExecute(self):

        self.mLogInfo("Creating Atp Ini file for future scan listener setup.")

        if self.__customerNetwork is None:
            self.mLogWarn("Customer network info is None")
            return

        _found = False
        for _node in self.__customerNetwork['nodes']:
            self.mLogInfo(json.dumps(_node))
            self.mLogInfo(self.__domu)
            if _node["client"]["hostname"] == self.__domu.split('.')[0]:
                _backup = _node["backup"]
                _backup["scanname"] = ebAtpUtils.mGetDictFromGen2Payload(self.__customerNetwork, "backup_scans/hostname" )
                _backup["scanip"] = ebAtpUtils.mGetDictFromGen2Payload(self.__customerNetwork, "backup_scans/ips")[0]
                _backup["dnsdomainnames"] = ebAtpUtils.mGetDictFromGen2Payload(self.__customerNetwork, "network_services/backupdns/domain_name")
                _backup["dnsdomainips"] = ebAtpUtils.mGetDictFromGen2Payload(self.__customerNetwork, "network_services/backupdns/ip")
                ##Assuming we only have one dns for OCI
                _backup["dnsserver"] = ebAtpUtils.mGetDictFromGen2Payload(self.__customerNetwork, "network_services/dns")[0]
                _backup["dbSystemOCID"] = self._atp.mGetATPOption('dbSystemOCID')
                self.mLogInfo("Writing ATP ini file on %s" % self.__domu)
                _found = True
                ebAtpUtils.mWriteAtpIniFile(_backup, self.__domu)

        if not _found:
            self.mLogInfo("Node %s not found in ATP ini payload" % self.__domu)

class AtpSetupASMListener(ebAtpStep):

    def __init__(self, aNode, aCluCtrlObj, aDbName):
        ebAtpStep.__init__(self, aNode, aCluCtrlObj.mGetATP())
        self.__ebox = aCluCtrlObj
        self.__pair = aCluCtrlObj.mReturnDom0DomUPair()
        self.__dbname = aDbName
        self.__machines = aCluCtrlObj.mGetMachines()
        self.__networks = aCluCtrlObj.mGetNetworks()
        self.__clusters = aCluCtrlObj.mGetClusters
        self.__options = aCluCtrlObj.mGetArgsOptions()

    def _mExecute(self):
        # BUG 32097088: Ensure ASM Instance is up before setup
        _domus = [ domu for _, domu in self.__pair ]
        self.__ebox.mCheckCrsIsUp(_domus[0], _domus)
        self.__ebox.mCheckAsmIsUp(_domus[0], _domus)

        self.mLogInfo("Update ASM local_listener on each node to LISTENER_BKUP VIP")
        ## Update ASM local_listener on each node to LISTENER_BKUP VIP
        _dom0,_domU = self.__pair[0]
        for _dom0, _domU in self.__pair:
            _sid = ebAtpUtils.mGetOracleSid(_domU, 'ASM')
            # do not use mGetBackupVipFromAtpIni as atp.ini is the pre-namespace mappings
            #_backupVip = ebAtpUtils.mGetBackupVipFromAtpIni(_domU)
            _nodeDomU = exaBoxNode(get_gcontext())
            _nodeDomU.mSetUser('grid')
            _nodeDomU.mConnect(aHost=_domU)
            _cmd_run_as_grid="lsnrctl status listener_bkup|grep \"HOST=\"|tr '(' '\n'|grep \"HOST=\"|tr -d ')'|cut -d= -f2"
            _backupVip = ""
            _i, _o, _e = _nodeDomU.mExecuteCmd(_cmd_run_as_grid)
            if _o:
                _out = _o.readlines()
                if not _out:
                    raise ExacloudRuntimeError(0x0873, 0x0A, 'ASM instance not found.')
                _backupVip = _out[0].strip()
            else:
                raise ExacloudRuntimeError(0x0873, 0x0A, 'AtpSetupASMListener failed, ' + _e.read())
            self.mLogInfo(" _sid %s. " % _sid)
            self.mLogInfo(" _backupVip %s. " % _backupVip)
            # Note:alter system register is done in next block to execute it just once
            _cmd_run_as_grid="echo \"ALTER SYSTEM SET LOCAL_LISTENER='(ADDRESS=(PROTOCOL=TCP)(HOST="   +   _backupVip   +   ")(PORT="   +   "1522"   +    "))' SCOPE=BOTH SID='"  +     _sid   +    "';\" | sqlplus -s / as sysasm"
            self.mLogInfo(" Running %s. " % _cmd_run_as_grid)
            #_expectedOutput =  "System altered."
            _i, _o, _e = _nodeDomU.mExecuteCmd(_cmd_run_as_grid)
            _nodeDomU.mDisconnect()

        _dom0,_domU = self.__pair[0]
        self.mLogInfo("DomU to run ASM Listener update: %s"%(_domU))
        GRID_ORACLE_HOME=ebAtpUtils.mGetOracleHome(_domU, 'grid')
        self.mLogInfo("GRID_ORACLE_HOME= %s"%(GRID_ORACLE_HOME))
        _nodeDomU = exaBoxNode(get_gcontext())
        _nodeDomU.mSetUser('grid')
        _nodeDomU.mConnect(aHost=_domU)
        # Registering ASM instances to listener updated in previous block
        _cmd_run_as_grid="echo \"ALTER SYSTEM REGISTER;\" | sqlplus -s / as sysasm"
        _i, _o, _e = _nodeDomU.mExecuteCmd(_cmd_run_as_grid)
        _cmd_run_as_grid = GRID_ORACLE_HOME+"/bin/crsctl modify resourcegroup ora.asmgroup -attr \"START_DEPENDENCIES='weak(global:ora.gns,ora.LISTENER_BKUP.lsnr) dispersion:active(site:type:ora.asmgroup.gtype)'\" -unsupported "
        _i, _o, _e = _nodeDomU.mExecuteCmd(_cmd_run_as_grid)
        _nodeDomU.mDisconnect()
        if _o:
            self.mLogInfo("Updated ASM Group START_DEPENDENCIES")
            ## Restart the cluster on all nodes for ASM Listener changes to take effect
            _nodeDomU = exaBoxNode(get_gcontext())
            _nodeDomU.mSetUser('root')
            _nodeDomU.mConnect(aHost=_domU)
            self.mLogInfo("Stopping cluster on all nodes")
            _cmd_stop_crs_all = GRID_ORACLE_HOME+"/bin/crsctl stop cluster -all"
            _i, _o, _e = _nodeDomU.mExecuteCmd(_cmd_stop_crs_all)
            if _o:
                self.mLogInfo("Command %s executed successfully"%(_cmd_stop_crs_all))
                _cmd_start_crs_all = GRID_ORACLE_HOME+"/bin/crsctl start cluster -all"
                self.mLogInfo("Starting cluster on all nodes")
                _i, _o, _e = _nodeDomU.mExecuteCmd(_cmd_start_crs_all)
                if _o:
                    self.mLogInfo("Command %s executed successfully"%(_cmd_start_crs_all))
            _nodeDomU.mDisconnect()
        else:
            self.mLogError("Command %s not executed"%(_cmd_run_as_grid))


class AtpSetupNamespace(ebAtpStep):
    ''' Call this to setup network namespace for ATP'''
    
    def __init__(self, aNode, aAtp, aCustomerNetwork, aDomU):
        ebAtpStep.__init__(self, aNode, aAtp)
        self.__customerNetwork = aCustomerNetwork
        self.__domu = aDomU

    def _mExecute(self):
        self.mLogInfo("Create config file for consumption by namespace rpm")
        if self.__customerNetwork is None:
            self.mLogWarn("Customer network info is None")
            return

        _found = None
        for _node in self.__customerNetwork['nodes']:
            self.mLogInfo(json.dumps(_node))
            self.mLogInfo(self.__domu)
            if _node["client"]["hostname"] == self.__domu.split('.')[0]:
                self.mLogInfo("Writing ATP Setup Namespace file on %s" % self.__domu)
                _found = { 'nodes' : self.__customerNetwork['nodes'] }
                ebAtpUtils.mWriteAtpNamespaceFile(_found, self.__domu)

        if not _found:
            self.mLogInfo("Node %s not found in payload ATP Setup Namespace" % self.__domu)


class ebATPNetworkUtils(object):

    @staticmethod
    def mATPGetNetwork(aNetList, aIFType, aNetworks):
        for _net in aNetList:
            if '_' + aIFType in _net:
               return aNetworks.mGetNetworkConfig(_net)

    @staticmethod
    def mATPGetBackupNetworkConfig(aNetList, aNetworks):
        return ebATPNetworkUtils.mATPGetNetwork(aNetList, 'backup', aNetworks)

    @staticmethod
    def mATPGetClientNetworkConfig(aNetList, aNetworks):
        return ebATPNetworkUtils.mATPGetNetwork(aNetList, 'client', aNetworks)

class ebATPTest(object):

    @staticmethod
    def mAtpTest(ddp, aOptions, machines, networks, aClusters):
        ebLogInfo("Running Post VM ATP Steps...")
        _atp = ebCluATPConfig(aOptions)
        for _dom0, _domU in ddp:
            with connect_to_host(_domU, get_gcontext()) as _node:
                #
                # Revert vm.cfg to previous and delete u02 img
                #
                # self.__isATP = True

                ebLogInfo("Running Post VM ATP Steps on %s" % _domU)
                AtpAddRoutes2DomU(_node, _atp, _domU, ddp, machines, networks).mExecute()
                # ips=ebAtpUtils.mGetClientIps(ddp, machines, networks, _domU)
                # _vip_lists = ebAtpUtils.mGetClientVip(aClusters, machines, _domU)
                _dbname = ebAtpUtils.mGetExaboxATPOption("test_db_name")
                ebLogInfo("_dbname: %s" % _dbname)

                _domU_mac = machines.mGetMachineConfig(_domU)
                _domU_net_list = _domU_mac.mGetMacNetworks()
                #ebLogInfo(ebATPNetworkUtils.mATPGetBackupNetworkConfig(_domU_net_list, networks).mGetNetMaster())
                #ebLogInfo(ebATPNetworkUtils.mATPGetBackupNetworkConfig(_domU_net_list, networks).mGetNetMask())
                ebLogInfo(ebATPNetworkUtils.mATPGetBackupNetworkConfig(_domU_net_list, networks).mGetNetIpAddr())
                # AtpDisableSshOnClientIFDomU(_node, _atp, _domU).mExecute()
            
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _domUMacs = ebAtpUtils.mGetBackupMac(ddp, machines, networks, _domU)
                #ebLogInfo(_domUMacs)
                #AtpCreateAtpIni(_node, _atp, aOptions.jsonconf["customer_network"], _domU).mExecute()
                #AtpAddiptables2Dom0(_node, _atp, ddp, machines, networks).mExecute()
                #AtpAddScanname2EtcHosts(_node, _atp, _domU).mExecute()

        _dom0, _domU = ddp[0]
        with connect_to_host(_domU, get_gcontext()) as _node:
            pass

        #AtpSetupSecondListener(_node, _atp, ddp, machines, networks, "atptest", aClusters, aOptions).mExecute()
