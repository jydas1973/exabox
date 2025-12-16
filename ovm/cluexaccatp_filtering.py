"""
 Copyright (c) 2018, 2023, Oracle and/or its affiliates.

NAME:
    cluexaccatp_filtering.py - Exacloud ATP Iptables Logic

FUNCTION:
    Setup CPS IB

NOTE:

History:

    MODIFIED   (MM/DD/YY)
       aararora 08/21/23 - Bug 35685169: Remove nft commands for generating
                           ebtables rules.
       aararora 08/02/23 - Bug 35665988: Correct added IN and OUT rules for
                           ADB-CC.
       jesandov 07/12/23 - 35566155: Persist of ebtables rules on OL8
       aararora 04/07/23 - Bug 35256867: The rule name should be shortened to within 28
                           characters.
       jesandov 03/31/23 - 35188255 - Add prefix to ebtables in ExaCC ATP
       hnvenkat 09/17/20 - XbranchMerge hnvenkat_bug-31889968 from
                           st_ecs_19.4.3.3.1
       hnvenkat 09/16/20 - 31889968. Send KVM flag to mProcessDom0
       vgerard  03/20/20 - Creation 
"""

import ipaddress
import json
import os
import tempfile
import re
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.ovm.cluexaccutils import ebOCPSJSONReader
from exabox.ovm.cluexaccatp import ATPEXACC_NATVIPFILE

ATPEXACC_DOMU_NETWORK_INFO='/opt/exacloud/atpcc_nodes'
ATPEXACC_DOMU_ATP_INFO='/opt/exacloud/atpcc_info'
ATPEXACC_NETWORK_DOM0_FILTERS_PATH='/opt/exacloud/atpcc/'
ATPEXACC_NETWORK_DOM0_MACINFO='/opt/exacloud/atpcc/{}_macinfo'
ATPEXACC_NETWORK_DOM0_LOCALMAC='/opt/exacloud/atpcc/{}_localmac'
ATPEXACC_NETWORK_DOM0_EBTABLES='/opt/exacloud/atpcc/{}_ebtables'




class ebExaCCAtpFiltering(object):
    """
       Setup domU rules for Client/Backup, and dom0 rules for Admin/NAT
    """

    @staticmethod
    def sCleanupDom0EBtables(aNode, aDomU):
        ebLogInfo('*** Cleaning up ExaCC-OCI EBtables for domU: {}'.format(aDomU))
        _hostname = aDomU.split('.')[0]
        _filename = ATPEXACC_NETWORK_DOM0_EBTABLES.format(_hostname)
        aNode.mExecuteCmd("sh {}_cleanup".format(_filename))
        aNode.mExecuteCmd("rm -f {}/{}_*".format(
                          ATPEXACC_NETWORK_DOM0_FILTERS_PATH,_hostname))


    def __init__(self, aPayload, aDebug=False, aTestMode=False):
        """
           :param dict aCustomerNetwork: customer_network section of create
                                         service payload
        """
        self.__dom0_mac_data = {}
        self.__customer_network_payload = aPayload.get('customer_network',{})
        self.__nodes_number = len(self.__customer_network_payload.get('nodes',[]))

        self.__saved_fields = {}
        if 'atp' in aPayload and 'vmClusterOcid' in aPayload['atp']:
            self.__saved_fields['vmClusterOcid'] = aPayload['atp']['vmClusterOcid']
        if 'dbaas_api' in aPayload and 'params' in aPayload['dbaas_api']:
            if 'cns' in aPayload['dbaas_api']['params']:
                self.__saved_fields['cns'] = aPayload['dbaas_api']['params']['cns']
        
        # Allow dom0 processing only when processed_domU == nodes_number
        self.__processed_domUs = 0
        
        # Read values from OCPS Json
        _ocps_json = ebOCPSJSONReader()
        self.__CPSAdminIPs   = _ocps_json.mGetCPSAdminIps()
        self.__adminServices = _ocps_json.mGetServices()

        self.__debug = aDebug
        self.__test_mode = aTestMode


    def mSetDom0MacData(self, aMacData):
        """
           Mostly a test hook
        """
        self.__dom0_mac_data = aMacData

    def mReadOnDom0OtherDomUATPMacs(self, aDom0Node):
        """
           Return a Set of unique MAC for every created ATP domU 
           (/opt/exacloud/atpcc/{}_localmac exists)
        """
        _atp_macs = set()
        if self.__test_mode:
            return _atp_macs
        # Look for all ATP configs /opt/exacloud/atpcc/*_localmac
        _i, _o, _r = aDom0Node.mExecuteCmd('cat ' + ATPEXACC_NETWORK_DOM0_LOCALMAC.format('*'))
        if _o:
            _atp_macs = set()
            _out = _o.readlines()
            for _mac in _out:
                _atp_macs.add(_mac.strip())

        return _atp_macs


    def mProcessDom0(self, aDom0Node, aDomUHostname, aIsKvm=False):
        """
           Process dom0 ebtables/iptables for ATP Admin Network security
        """
        # Standard create service will have a Customer Network payload and 
        # Node number above 0, allow this function to be run without payload
        if not self.__test_mode and self.__nodes_number > 0 and \
           (self.__processed_domUs != self.__nodes_number):
            raise ValueError("Please process all domU until setting up dom0 filtering")

        _hostname = aDomUHostname.split('.')[0].strip() #Ensure Short hostname_

        # Set default ebtables rules for ATP-CC
        # Clear and Set back INPUT, a short rule flickr is better than leftovers or accumulation

        # Dom0 should be unreachable, except from lo/eth0, build script
        # INPUT CHAIN (do not touch default policy, that allow chain to be flushed)
        _cmds  = ['ebtables -F INPUT', 'ebtables -F OUTPUT']
        
        _own_vm_mac = ''
        _other_vm_macs = []

        for _vms in self.__dom0_mac_data:
            _mac = self.__dom0_mac_data[_vms]['admin_mac']
            if _vms == _hostname:
                _own_vm_mac = _mac
            else:
                _other_vm_macs.append(_mac)
        _other_vm_macs.sort()

        if not _own_vm_mac:
            ebLogError('DomU {} is not present in the mac table: {}'.format(_hostname, self.__dom0_mac_data))
            raise ValueError('DomU {} not found'.format(_hostname))

        # DROP local MAC and other ATP MACS
        _atp_macs = self.mReadOnDom0OtherDomUATPMacs(aDom0Node)
        _atp_macs.add(_own_vm_mac)

        _hostOL8 = False
        aDom0Node.mExecuteCmd("/bin/cat /etc/oracle-release | /bin/grep 'elease 8'")
        if aDom0Node.mGetCmdExitStatus() == 0:
            _hostOL8 = True

        _drop_other_atp_vms = []
        _drop_current_vm = []

        for _atp_mac in _atp_macs:
            if _atp_mac == _own_vm_mac:
                _li = _drop_current_vm  #  Current ATP vm
            else:
                _li = _drop_other_atp_vms # Other VMs must be kept on cleanup
            _li.append('ebtables -A INPUT -s {} -j DROP'.format(_atp_mac))
            _li.append('ebtables -A OUTPUT -d {} -j DROP'.format(_atp_mac))
        
        _chain_key = "ATP{0}".format(_own_vm_mac.replace(':','').upper())
        _chain_suffixes = ('IN','IN_FROM_CPS','OUT','OUT_TO_CPS')
        # Base Forwards (if source MAC match -> OUT CHAIN, if dest MAC -> IN)
        _base_fwds = ('-d {} -i eth0 -j {}_IN'.format(_own_vm_mac, _chain_key),
                      '-s {} -j {}_OUT'.format(_own_vm_mac,_chain_key))

        # Remove leftover jumps
        _cmds_chain_removal  = ['ebtables -D FORWARD {}'.format(x) for x in _base_fwds]
        _cmds_chain_creation = []

        for _suffix in _chain_suffixes:
            _chain_name = '{}_{}'.format(_chain_key,_suffix)
            _cmds_chain_removal.append('ebtables -X {}'.format(_chain_name))
            _cmds_chain_creation.append('ebtables -N {} -P DROP'.format(_chain_name))

        #Remove then create
        _cmds += _drop_other_atp_vms
        _cmds += _cmds_chain_removal
        
        # COPY THE LIST TO HAVE THE CLEANUP COMMANDS FOR DELETE SERVICE
        _cleanup_cmds = list(_cmds)
        
        _cmds += _drop_current_vm
        _cmds += _cmds_chain_creation

        _cmds += ['ebtables -A FORWARD {}'.format(x) for x in _base_fwds]

        # ALLOW ARP + other vms !!!OF SAME CLUSTER!!! by MAC

        _cmds.append('ebtables -A {}_IN -p ARP -j ACCEPT'.format(_chain_key))
        _cmds.append('ebtables -A {}_OUT -p ARP -j ACCEPT'.format(_chain_key))
        if len(_other_vm_macs) == 1: #QTR Rack
            _cmds.append('ebtables -A {}_IN -s {} -j ACCEPT'.format(
                            _chain_key,_other_vm_macs[0]))
            _cmds.append('ebtables -A {}_OUT -d {} -j ACCEPT'.format(
                            _chain_key,_other_vm_macs[0]))
        else: # Other shapes
            for _mac_vm in _other_vm_macs:
                _cmds.append('ebtables -A {}_IN -s {} -j ACCEPT'.format(
                                _chain_key,_mac_vm))
                _cmds.append('ebtables -A {}_OUT -d {} -j ACCEPT'.format(
                                _chain_key,_mac_vm))

        # ALLOW CPS<->DomU On port TCP 22 and ICMP
        for _cps_ip in self.__CPSAdminIPs:
            _cmds.append('ebtables -A {0}_IN -p IPv4 --ip-src {1} -j {0}_IN_FROM_CPS'.format(_chain_key, _cps_ip))
            _cmds.append('ebtables -A {0}_OUT -p IPv4 --ip-dst {1} -j {0}_OUT_TO_CPS'.format(_chain_key, _cps_ip))

        # CPS IN RULES
        _cmds.append('ebtables -A {}_IN_FROM_CPS -p IPv4 --ip-proto icmp -j ACCEPT'.format(_chain_key))
        _cmds.append('ebtables -A {}_IN_FROM_CPS -p IPv4 --ip-proto tcp --ip-dport 22 -j ACCEPT'.format(_chain_key))

        # CPS OUT RULES
        _cmds.append('ebtables -A {}_OUT_TO_CPS -p IPv4 --ip-proto icmp -j ACCEPT'.format(_chain_key))
        _cmds.append('ebtables -A {}_OUT_TO_CPS -p IPv4 --ip-proto tcp --ip-sport 22 -j ACCEPT'.format(_chain_key))

        # DOCKER SERVICES RULES
        for _, _service in self.__adminServices.items():
            _ip, _port = _service['ip'], _service['port']
            _cmds.append('ebtables -A {}_IN -p IPv4 --ip-src {} --ip-proto tcp --ip-sport {} -j ACCEPT'.format(
                         _chain_key, _ip, _port))
            _cmds.append('ebtables -A {}_OUT -p IPv4 --ip-dst {} --ip-proto tcp --ip-dport {} -j ACCEPT'.format(
                         _chain_key, _ip, _port))
        
        if self.__debug:
            ebLogDebug("Generated dom0 EBtables for domU {} :\n{}".format(
                        _hostname, _cmds))
        # Test hook
        if self.__test_mode:
            return _cmds

        _tmpfile =  tempfile.NamedTemporaryFile(delete=False)
        _tmpfile2 =  tempfile.NamedTemporaryFile(delete=False)
        _tmpfile3 =  tempfile.NamedTemporaryFile(delete=False)
        try:
            # WRITE INFO to Dom0 for debugging / cleanup purpose
            _tmpfile.write(json.dumps(self.__dom0_mac_data).encode('utf8'))
            _tmpfile.close()
            _tmpfile2.write('\n'.join(_cmds).encode('utf8'))
            _tmpfile2.close()
            _tmpfile3.write('\n'.join(_cleanup_cmds).encode('utf8'))
            _tmpfile3.close()
            aDom0Node.mExecuteCmd('mkdir -p {}'.format(ATPEXACC_NETWORK_DOM0_FILTERS_PATH))
            aDom0Node.mCopyFile(_tmpfile.name, ATPEXACC_NETWORK_DOM0_MACINFO.format(_hostname))
            _dom0_filename = ATPEXACC_NETWORK_DOM0_EBTABLES.format(_hostname)
            aDom0Node.mCopyFile(_tmpfile2.name,_dom0_filename )
            aDom0Node.mCopyFile(_tmpfile3.name,_dom0_filename + '_cleanup')
            ebLogInfo('Setting up ATP Ebtables rules for Admin network for domU {}'.format(_hostname))
            aDom0Node.mExecuteCmd('sh {}'.format(_dom0_filename))
            _localmac_filename = ATPEXACC_NETWORK_DOM0_LOCALMAC.format(_hostname)
            aDom0Node.mExecuteCmd('echo "{}" > {}'.format(_own_vm_mac,_localmac_filename))
            # Service save is supported on both OL7/OL6 dom0s
            if aIsKvm:
                aDom0Node.mExecuteCmd('/usr/libexec/ebtables save')
            else:
                aDom0Node.mExecuteCmd('service ebtables save')

            if _hostOL8:
                aDom0Node.mExecuteCmdLog('/bin/cp /etc/nftables/exadata.nft /etc/nftables/exadata.`date +%y.%j.%H.%m.%s`')
                aDom0Node.mExecuteCmdLog('/usr/sbin/nft list ruleset > /etc/nftables/exadata.nft')


        finally:
            os.remove(_tmpfile.name)
            os.remove(_tmpfile2.name)
            os.remove(_tmpfile3.name)

    def mProcessDomU(self, aDomUNode):
        """
            Process a single domU, and fetch its Mac address for dom0 filtering
        """
        self.mWriteInfoToDomU(aDomUNode, self.__customer_network_payload,
                             ATPEXACC_DOMU_NETWORK_INFO)
        if self.__saved_fields:
            self.mWriteInfoToDomU(aDomUNode, self.__saved_fields,
                             ATPEXACC_DOMU_ATP_INFO)
        self.mBuildMacAddressData(aDomUNode)
        self.__processed_domUs += 1
    
    def mBuildMacAddressData(self, aDomUNode):
        _eth0_mac = aDomUNode.mSingleLineOutput("cat /sys/class/net/eth0/address")
        _domu_hostname = aDomUNode.mSingleLineOutput("hostname -s")
        self.__dom0_mac_data[_domu_hostname.strip()] = {'admin_mac':_eth0_mac.strip()}


    def mWriteInfoToDomU(self, aDomUNode, aObject, aFilename):
        """
            Write the nodes section of the payload to the domU for iptables generation

            :param object aDomUNode: Connected domU exaBoxNode
            :param dict aObject : Dictionary object to write
            :param str aFilename : domU Filename
        """
        _tmpfile =  tempfile.NamedTemporaryFile(delete=False)
        try:
            _tmpfile.write(json.dumps(aObject).encode('utf8'))
            _tmpfile.close()
            # If NAT-VIPs are not present, this is the first time /opt/exacloud is used
            aDomUNode.mExecuteCmd('mkdir -p {}'.format(os.path.dirname(aFilename)))
            aDomUNode.mCopyFile(_tmpfile.name, aFilename)
            aDomUNode.mExecuteCmd('chown opc:opc {}'.format(aFilename))
        finally:
            os.remove(_tmpfile.name)

    # VERY Basic rules for now on CC ATP domU, to be refined
    @staticmethod
    def sSetDomURules(aDomUNode):
        _cmd_atpccips = "cat {}".format(ATPEXACC_NATVIPFILE)
        _atpccips_str =  aDomUNode.mSingleLineOutput(_cmd_atpccips)
        _domu_hostname = aDomUNode.mSingleLineOutput('hostname').split('.')[0].strip()
        _atpccips     = []
        try:
            # Dictionary containing adminip/clienthn info for all nodes 
            _atpccips = json.loads(_atpccips_str)
        except:
            ebLogWarn("*** Could not decode NATATP Info info from ({}) output: {}".format(_cmd_atpccips, _atpccips_str))
            ebLogWarn("*** SSH will not be redirected through Admin network")
 
        _rules = []
        _rules += ['-A INPUT -i lo -j ACCEPT',
                   '-A INPUT -i bondeth0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT',
                   '-A INPUT -i bondeth1 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT',
                   '-A INPUT -i bondeth0 -p tcp -m tcp --dport 1521 -j ACCEPT',
                   '-A INPUT -i bondeth0 -p tcp -m tcp --dport 443 -j ACCEPT',
                   '-A INPUT -i bondeth0 -p tcp -m tcp --dport 2484 -j ACCEPT',
                   '-A INPUT -i bondeth0 -p tcp -m tcp --dport 6200 -j ACCEPT',
                   '-A INPUT -i bondeth1 -j DROP']

        _nat_rules = []
        _mangle_rules = []
        _own_admin = None
        if _atpccips: #CAN Only Block Client net if Admin network is setup properly for redirections
            _rules.append('-A INPUT -i bondeth0 -j DROP')
            for _atpcc_host in _atpccips:
                # Do not NAT local connections
                if _atpcc_host['clienthn'].strip() == _domu_hostname:
                    _own_admin = _atpcc_host['adminip']
                    continue
                # iptables will resolve the hostname and insert it as an IP
                # (iptables-save will show all ip)
                _nat_rules.append("-A OUTPUT -d '{}' -o bondeth0 -p tcp -m tcp --dport 22 -j DNAT --to-destination {}".format(
                                  _atpcc_host['clienthn'],_atpcc_host['adminip']))
                _nat_rules.append("-A OUTPUT -d '{}' -o bondeth0 -p icmp -j DNAT --to-destination {}".format(
                                  _atpcc_host['clienthn'],_atpcc_host['adminip']))
                # Mark SSH packets that would need to be routed through eth0
                _mangle_rules.append("-A OUTPUT -d '{}' -o bondeth0 -p tcp -m tcp --dport 22 -j MARK --set-xmark 0x16".format(
                                  _atpcc_host['clienthn']))
                _mangle_rules.append("-A OUTPUT -d '{}' -o bondeth0 -p icmp -j MARK --set-xmark 0x16".format(
                                  _atpcc_host['clienthn']))

            if _nat_rules and _own_admin:
                # Static Masquerading
                _nat_rules.append("-A POSTROUTING -o eth0 -p tcp -m tcp --dport 22 -j SNAT --to-source {}".format(_own_admin))
                _nat_rules.append("-A POSTROUTING -o eth0 -p icmp -j SNAT --to-source {}".format(_own_admin))

        for _iptable_cmd in _rules:
            aDomUNode.mExecuteCmd('iptables ' + _iptable_cmd)

        for _iptable_nat_cmd in _nat_rules:
            aDomUNode.mExecuteCmd('iptables -t nat ' + _iptable_nat_cmd)

        for _iptable_mangle_cmd in _mangle_rules:
            aDomUNode.mExecuteCmd('iptables -t mangle ' + _iptable_mangle_cmd)

        # Having packets originating from one if and comming to another confuse rp filtering
        # Disable it for eth0

        aDomUNode.mExecuteCmd("sed -i 's/^net.ipv4.conf.eth0.rp_filter.*/net.ipv4.conf.eth0.rp_filter = 0/' /etc/sysctl.conf")
        aDomUNode.mExecuteCmd("sysctl -w net.ipv4.conf.eth0.rp_filter=0")

        if not _mangle_rules:
            # ALL BELOW PART ONLY APPLY IF ROUTE REDIRECTION IS SETUP
            return

        _route_id = None
        # Setup transparent redirection of marked packets
        _, _o, _e = aDomUNode.mExecuteCmd('cat /etc/sysconfig/network-scripts/route-eth0')
        _out = _o.readlines()
        if _out:
            # capture () the route number: <space>table<space>(NUMBERS)
            r = re.compile(r".*\s+table\s+(\d+)")
            for _line in _out:
                _routematch = r.match(_line)
                if _routematch:
                    _route_id = _routematch.groups()[0]
                    break

        if _route_id:
            aDomUNode.mExecuteCmd("sh -c 'echo fwmark 0x16 table {} >> /etc/sysconfig/network-scripts/rule-bondeth0'".format(_route_id))
            aDomUNode.mExecuteCmd("ip rule add fwmark 0x16 table {}".format(_route_id))


