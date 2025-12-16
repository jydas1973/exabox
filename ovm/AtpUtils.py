import socket
import struct, json, os, re
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.utils.node import connect_to_host, node_exec_cmd, node_cmd_abs_path_check

class ebAtpUtils(object):

    EXACLOUD_CONFIG_DIR = "/opt/exacloud"
    ATP_INI_FILE = EXACLOUD_CONFIG_DIR + "/atp.ini"
    ATP_NAMESPACE_NODES_FILE = EXACLOUD_CONFIG_DIR + "/nodes.json"
    DOM0_EXACLOUD_CONFIG_NETWORK_DIR = EXACLOUD_CONFIG_DIR + "/network"
    DOM0_VIF_INFO_FILE=DOM0_EXACLOUD_CONFIG_NETWORK_DIR + "/vif-all-client-ips"

    @staticmethod
    def cidr_to_netmask(cidr):
        network, net_bits = cidr.split('/')
        host_bits = 32 - int(net_bits)
        netmask = socket.inet_ntoa(struct.pack('!I', (1 << 32) - (1 << host_bits)))
        return network, netmask
    @staticmethod
    def isCidr(cidr):
        _pattern = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$'
        return bool(re.match(_pattern, cidr))

    @staticmethod
    def isIP4(ip4):
        _pattern = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
        return bool(re.match(_pattern, ip4))

    @staticmethod
    def mGetSubnetFromIpAndNetmask(aIP, aNetmask):
        _ip = aIP
        _mask = aNetmask
        _subnet = '.'.join([str(int(octet) & int(masked)) for octet, masked in zip(_ip.split('.'), _mask.split('.'))])
        return _subnet

    ##Use DBAASTOOL to determine if VM is ATP or not
    @staticmethod
    def isVMAtp(aDomU):
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDomU)
        _,_o,_ = _node.mExecuteCmd('/var/opt/oracle/ocde/rops atp_enabled')
        _rc = (_o and '1' in _o.read().strip()) # is ATP
        _node.mDisconnect()
        return _rc

    @staticmethod
    def getScanName(nodeDomU, srvctl_bin):
        _cmd_scanName = f"{srvctl_bin} config scan | /bin/grep '^SCAN name'"
        _, _out, _ = nodeDomU.mExecuteCmd(_cmd_scanName)
        _out = _out.read().split(',')[0]
        _out = _out.split()
        _scanName = _out[2]
        return _scanName

    @staticmethod
    def setScanFqdn(dpairs):
        ebLogInfo("*** Modifying scan name on the DOMU ***")
        _dom0, _domU = dpairs[0]
        _grid_home = ebAtpUtils.mGetOracleHome(_domU, 'grid')
        _srvctl_bin = f"{_grid_home}/bin/srvctl"
        _nodeDomU = exaBoxNode(get_gcontext())
        _nodeDomU.mConnect(aHost=_domU)
        _scanName = ebAtpUtils.getScanName(_nodeDomU, _srvctl_bin)
        _cmd_domainName = "/bin/hostname -d"
        _, _out, _ = _nodeDomU.mExecuteCmd(_cmd_domainName)
        _domainName = _out.read().strip()
        if _domainName in _scanName:
            ebLogInfo(f"*** Scan name on the DOMU is already in fqdn format: {_scanName}. ***")
            return
        _scanFqdn = _scanName + '.' + _domainName
        _cmd_modifyScanName = f"{_srvctl_bin} modify scan -scanname {_scanFqdn}"
        _, _out, _ = _nodeDomU.mExecuteCmd(_cmd_modifyScanName)
        _scanName = ebAtpUtils.getScanName(_nodeDomU, _srvctl_bin)
        if _scanFqdn == _scanName:
            ebLogInfo(f"*** Modified scan name on the DOMU to scan fqdn: {_scanName}. ***")
        else:
            ebLogError(f"*** Could not modify scan name on the DOMU to scan fqdn: {_scanFqdn}. ***")
        _nodeDomU.mDisconnect()

    @staticmethod
    def mGetOracleHome(aDomU, aDbName):
        """
        :param aDomU: domU
        :param aOType: 'grid' or dbname
        :return: oracle home string or None
        """
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDomU)
        _oracle_home = None
        if aDbName == 'grid':
            _cmd_str = "cat /etc/oratab | grep '^+.*' "
        else:
            _cmd_str = "cat /etc/oratab | grep '^%s:' " % aDbName
        ebLogInfo(_cmd_str)
        _, _out, _ = _node.mExecuteCmd(_cmd_str)
        _out = _out.readlines()
        if (_out is not None and len(_out) != 0):
            _oracle_home = _out[0].split(":")[1].strip()
        _node.mDisconnect()
        return _oracle_home

    @staticmethod
    def mGetOracleSid(aDomU, aDbName, aConnectedDomuMode=False):
        """
        :param aDomU: domU hostname in aConnectedDomuMode=False,
                      Connected exaBoxNode in ...........=True
        :param aDbName: dbname to use in grep, like 'ASM'
        :return: Sid or None
        """
        if not aConnectedDomuMode:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aDomU)
        else:
            _node = aDomU
        _oracle_sid = None
        _cmd_str = """ps -efww |grep pmon |grep "%s[1-9]" |cut -d'_' -f3""" % aDbName
        ebLogInfo(_cmd_str)
        _, _out, _ = _node.mExecuteCmd(_cmd_str)
        _out = _out.readlines()
        if (_out is not None and len(_out) != 0):
            _oracle_sid = _out[0].strip()
        if not aConnectedDomuMode:
            _node.mDisconnect()
        return _oracle_sid

    @staticmethod
    def mCheckExaboxConfigOption(aOption, aValue=None):
        """
            mCheckExaboxConfigOption is refactored from ebExaboxCluCtrl Class member function
            It can be separated out from the class as it does not rely on any member parameters in the class
        """
        if aValue is None:
            if aOption in get_gcontext().mGetConfigOptions().keys():
                return get_gcontext().mGetConfigOptions()[aOption]
            else:
                return None

        if aOption in get_gcontext().mGetConfigOptions().keys():
            if get_gcontext().mGetConfigOptions()[aOption] == aValue:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def mGetExaboxATPOption(optionKey):
        """
            This static method checks exabox.conf for the following session:
            "atp": {
                "dom0_iptables": "True",
                "backup_ssh": "True",
                "domU_route": "True",
            }
        Returns True is the value of the key is "True"
        """
        _rtnValue = None
        _atpSettings = ebAtpUtils.mCheckExaboxConfigOption('atp')
        if _atpSettings:
            if optionKey in _atpSettings:
                _rtnValue = _atpSettings[optionKey]

        ebLogInfo("%s is set to %s in exabox.conf" % (optionKey, str(_rtnValue)))
        return _rtnValue

    @staticmethod
    def isFeatureEnabled(featureKey):
        """
            This static method checks exabox.conf for the following session:
            "atp": {
                "dom0_iptables": "True",
                "backup_ssh": "True",
                "domU_route": "True",
                "dnsmasq": "True"
        Returns True is the value of the key is "True"
        """
        ## Default to enable
        _rtnValue = True
        _atpSettings = ebAtpUtils.mGetExaboxATPOption(featureKey)
        if _atpSettings:
            if  _atpSettings == 'False':
                _rtnValue = False
        return _rtnValue

    @staticmethod
    def mGetIF2IPMapping(aPair, aMachines, aNetworks):
        """
        :param aPair:
        :param aMachines:
        :param aNetworks:
        :return: domU - client and backup ip mapping
        """
        _all_clients_ips = {
            'client' : {},
            'backup' : {}
        }

        for _dom0, _domU in aPair:

            _domU_mac = aMachines.mGetMachineConfig(_domU)
            _domU_net_list = _domU_mac.mGetMacNetworks()

            for _net in _domU_net_list:
                _priv = aNetworks.mGetNetworkConfig(_net)
                if _priv.mGetNetType() == 'client':
                    _all_clients_ips['client'][_domU] = _priv.mGetNetIpAddr()
                if _priv.mGetNetType() == 'backup':
                    _all_clients_ips['backup'][_domU] = _priv.mGetNetIpAddr()
        return _all_clients_ips

    @staticmethod
    def mGetIF2MacMapping(aPair, aMachines, aNetworks):
        """
        :param aPair:
        :param aMachines:
        :param aNetworks:
        :return: domU - client and backup ip mapping
        """
        _all_clients_macs = {
            'client': {},
            'backup': {}
        }

        for _dom0, _domU in aPair:

            _domU_mac = aMachines.mGetMachineConfig(_domU)
            _domU_net_list = _domU_mac.mGetMacNetworks()

            for _net in _domU_net_list:
                _priv = aNetworks.mGetNetworkConfig(_net)
                if _priv.mGetNetType() == 'client':
                    _all_clients_macs['client'][_domU] = _priv.mGetNetMacAddr()
                if _priv.mGetNetType() == 'backup':
                    _all_clients_macs['backup'][_domU] = _priv.mGetNetMacAddr()
        return _all_clients_macs

    @staticmethod
    def mGetIFNetmask(aPair, aMachines, aNetworks, aIFType, aDomU):
        """
        :param aPair:
        :param aMachines:
        :param aNetworks:
        :param aIFType: client/backup
        :return: netmask
        """
        _myNetmask = None
        for _dom0, _domU in aPair:
            if _domU == aDomU:
                _domU_mac = aMachines.mGetMachineConfig(_domU)
                _domU_net_list = _domU_mac.mGetMacNetworks()

                for _net in _domU_net_list:
                    _priv = aNetworks.mGetNetworkConfig(_net)
                    if _priv.mGetNetType() == aIFType:
                        _myNetmask = _priv.mGetNetMask()

        return _myNetmask
    @staticmethod
    def mGetIFGateway(aPair, aMachines, aNetworks, aIFType, aDomU):
        """
        :param aPair:
        :param aMachines:
        :param aNetworks:
        :param aIFType: client/backup
        :return: gateway
        """
        _myGateway = None
        for _dom0, _domU in aPair:
            if _domU == aDomU:
                _domU_mac = aMachines.mGetMachineConfig(_domU)
                _domU_net_list = _domU_mac.mGetMacNetworks()

                for _net in _domU_net_list:
                    _priv = aNetworks.mGetNetworkConfig(_net)
                    if _priv.mGetNetType() == aIFType:
                        _myGateway = _priv.mGetNetGateWay()

        return _myGateway

    @staticmethod
    def mGetBackupMac(aPair, aMachines, aNetworks, aDomU):
        _macs = ebAtpUtils.mGetIF2MacMapping(aPair, aMachines, aNetworks)
        return _macs['backup'][aDomU]

    @staticmethod
    def mGetClientMac(aPair, aMachines, aNetworks, aDomU):
        _macs = ebAtpUtils.mGetIF2MacMapping(aPair, aMachines, aNetworks)
        return _macs['client'][aDomU]

    @staticmethod
    def mGetIps(aPair, aMachines, aNetworks, aInterface, aUnwantedDomU=None, aWanted=None):
        """
        :param aPair:
        :param aMachines:
        :param aNetworks:
        :param aInterface: Valid values: 'client' or 'backup' only
        :param aMyDomU: if this is set, return IPs without domU
        :return: domU - client and backup ip mapping
        """
        _myClientIPs = ebAtpUtils.mGetIF2IPMapping(aPair, aMachines, aNetworks)[aInterface]
        _rtn_ips = []
        if aWanted is not None:
            return _myClientIPs[aWanted]
        if aUnwantedDomU is None:
            _rtn_ips = list(_myClientIPs.values())
        else:
            for key in _myClientIPs.keys():
                if key != aUnwantedDomU:
                    _rtn_ips.append(_myClientIPs[key])
        return _rtn_ips

    @staticmethod
    def mGetClientIps(aPair, aMachines, aNetworks, aUnwantedDomU=None):
        return ebAtpUtils.mGetIps(aPair, aMachines, aNetworks, 'client', aUnwantedDomU)

    @staticmethod
    def mGetBackupIps(aPair, aMachines, aNetworks, aUnwantedDomU=None, aWanted=None):
        return ebAtpUtils.mGetIps(aPair, aMachines, aNetworks, 'backup', aUnwantedDomU=aUnwantedDomU, aWanted=aWanted)

    @staticmethod
    def mGetVifFromDomUMac(aNodeDom0, aDomUHostname, aMac):
        _script="""
        domainID=`xm list |grep "{domU}"|awk '{{ print $2 }}'`; vif=`xm network-list $domainID|grep -i "{MacAddr}" |awk '{{ print $NF }}' | cut -d'/' -f6-`;echo "${{vif/\//}}" |tr '/' '.'
        """.format(domU=aDomUHostname, MacAddr=aMac)
        _, _o, _ = aNodeDom0.mExecuteCmd(_script)
        _vifName = _o.readlines()
        if 'vif' in str(_vifName):
            return _vifName[0].strip()
        else:
            ebLogError("*** ATP Cannot get VIF for %s with MAC: %s" % (aDomUHostname, aMac))
            return None

    @staticmethod
    def mGetClientVip(aClusters, aMachines, aDomU):

        #
        # Retrieve VIP IP (1 per VM)
        #
        _cname = aClusters.mGetClusters()
        _cnode = aClusters.mGetCluster(_cname[0])

        _vip_list  = _cnode.mGetCluVips()
        _clientvip = None
        for _vip in _vip_list.keys():
            _vip_name = _vip_list[_vip].mGetCVIPMachines()[0]
            _ip = _vip_list[_vip].mGetCVIPAddr()
            _mac_config = aMachines.mGetMachineConfig(_vip_name)
            _mac_name   = _mac_config.mGetMacHostName()
            if _mac_name == aDomU:
                _clientvip =_ip
                ebLogInfo("%s: %s - %s" % (aDomU, _vip, _ip))

        return _clientvip

    @staticmethod
    def mGetBackupInfo(aDomU, aElement, aNetType="backup"):

        _net = ebAtpUtils.mReadAtpIniFile2Dict(aDomU)
        ebLogInfo("*** ATP %s" % json.dumps(_net))
        _rtnValue = _net[aElement]
        ebLogInfo("*** ATP Getting %s value: %s" % (aElement, _rtnValue))
        return _rtnValue

    @staticmethod
    def mGetBackupVipFromAtpIni(aDomU):
        return ebAtpUtils.mGetBackupInfo(aDomU, 'vip')

    @staticmethod
    def mGetBackupScanIpFromAtpIni(aDomU):
        return  ebAtpUtils.mGetBackupInfo(aDomU, 'scanip')

    @staticmethod
    def mGetBackupScannameFromAtpIni(aDomU):
        return ebAtpUtils.mGetBackupInfo(aDomU, 'scanname')

    @staticmethod
    def mGetBackupGatewayFromAtpIni(aDomU):
        return ebAtpUtils.mGetBackupInfo(aDomU, 'gateway')

    @staticmethod
    ### aKeyStr can be "nodes/backup/gateway"
    ### or "backup_scans/hostname", etc
    def mGetDictFromGen2Payload(aCustomer_Network, aKeyStr):
        _keys = aKeyStr.split('/')
        _size = len(_keys)
        _rtnVal = aCustomer_Network
        for _key in _keys:
            try:
                _rtnVal = _rtnVal[_key]
                ebLogInfo("*** ATP key_value %s: %s" % (_key, _rtnVal))
            except:
                ebLogError("*** ATP cannot find value for %s" % aKeyStr)
        if _rtnVal == aCustomer_Network:
            return ""
        return _rtnVal 

    @staticmethod
    def mWriteAtpIniFile(aDict, aDomU):
        _filename = "/tmp/atp_%s.ini" % aDomU
        _atpIniFile = open(_filename, 'w')
        _atpIniFile.write(json.dumps(aDict))
        _atpIniFile.close()
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDomU)
        _node.mExecuteCmd("[ ! -e {atpinidir} ] && mkdir -p {atpinidir}".format(atpinidir=ebAtpUtils.EXACLOUD_CONFIG_DIR) )
        _node.mCopyFile(_filename, ebAtpUtils.ATP_INI_FILE)
        # Bug 37945713 - Set 644 permissions
        _bin_chmod = node_cmd_abs_path_check(_node, "chmod")
        _out_set_perms = node_exec_cmd(
            _node, f"{_bin_chmod} 644 {ebAtpUtils.ATP_INI_FILE}")
        ebLogTrace(_out_set_perms)
        _node.mDisconnect()
        os.remove(_filename)

    @staticmethod
    def mWriteAtpNamespaceFile(aDict, aDomU):
        # Writing the nodes from json payload into vm, for namespace rpm to consume
        _filename = "/tmp/nodes_%s.ini" % aDomU
        _atpNamespaceFile = open(_filename, 'w')
        _atpNamespaceFile.write(json.dumps(aDict, indent=4, sort_keys=True))
        _atpNamespaceFile.close()
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDomU)
        _node.mExecuteCmd("[ ! -e {atpconfdir} ] && mkdir -p {atpconfdir}".format(atpconfdir=ebAtpUtils.EXACLOUD_CONFIG_DIR) )
        _node.mCopyFile(_filename, ebAtpUtils.ATP_NAMESPACE_NODES_FILE)
        # Bug 37945713 - Set 644 permissions
        _bin_chmod = node_cmd_abs_path_check(_node, "chmod")
        _out_set_perms = node_exec_cmd(
            _node, f"{_bin_chmod} 644 {ebAtpUtils.ATP_NAMESPACE_NODES_FILE}")
        ebLogTrace(_out_set_perms)
        _node.mDisconnect()
        os.remove(_filename)


    @staticmethod
    def mReadAtpIniFile2Dict(aDomU):

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDomU)
        ebLogInfo("*** ATP Reading %s from %s" % (ebAtpUtils.ATP_INI_FILE, aDomU))
        _, _o, _err = _node.mExecuteCmd("cat " + ebAtpUtils.ATP_INI_FILE)
        _dictStr = _o.readlines()[0]
        ebLogInfo("*** ATP atp.ini: %s" % _dictStr)
        _node.mDisconnect()
        if _dictStr is None:
            ebLogError("Cannot read " + ebAtpUtils.ATP_INI_FILE)
            return None
        else:
            return json.loads(_dictStr)

    # Bug34266093: Update comment for future when StarterDB Code is removed.
    # once starterDB code is fully removed, this function can be deleted
    # Run the wallet_setup utility to generate grid and starterdb pwds in starterDB step.
    @staticmethod
    def mInstallAtpWallets(domUs, dbname):
        ebLogInfo("Installing ATP Wallets...")
        for _domu in domUs:
            ebLogInfo('ATP Wallets install for: {0}'.format(_domu))
            _username = 'oracle'
            with connect_to_host(_domu, get_gcontext(), username=_username) as _node:
                _node.mExecuteCmd("perl /var/opt/oracle/misc/atp/wallet_setup {0} rotatepwds".format(dbname))
            
            _username = 'grid'
            with connect_to_host(_domu, get_gcontext(), username=_username) as _node:
                _node.mExecuteCmd("perl /var/opt/oracle/misc/atp/wallet_setup grid")
