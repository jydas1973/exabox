"""
 Copyright (c) 2017, 2025, Oracle and/or its affiliates.

NAME:
    cluconncheck.py - Migrated code from sanity check script(developed by KDC team to help exacm quick deployment)
                      to exacloud for connectivity checks

FUNCTION:
    Provide API for sanity checks during provisioning

NOTE:
    #This implementation is just a quick and dirty way to include connectivity checks in exacloud and part of healthcheck log and reporting
    #TODO LIST: 
    # Modify ebXmlConfig to use clucontrol infra
    # replace print_csv to add check details in json report
    # Used some of hard code variable values and some unnecessary tweaks to just get it working to give rough idea
    # Remove method like check_ntp, check_route etc which are already in progress to be added in cluhealth
    # fix all issues / update connectivity check code as per production issues 
    # need a collaborative effort to build a common infra, which requires code refactor of healthcheck, precheck, connectivity check etc

History:
    ndesanto      10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    bhuvnkum      20/09/2017 - File Creation
"""

from __future__ import print_function

import six
import os, sys, subprocess, uuid, time, os.path, traceback
from datetime import datetime
import json
import threading

from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogSetHCLogDestination, ebLogRemoveHCLogDestination, ebLogHealth
from exabox.core.Context import get_gcontext

#class created temporarily to read xml in way connectivity expects and 
#later on modify to read it using clucontrol common infra
class ebXmlConfig(object):

    def __init__(self, aConfig):
        #attribute in machine will be filtered out except this list
        self.__attr_list = ['hostName','osType','id','networks', 'networkType',
                            'software', 'machine', 'DefaultGatewayNet',
                            'DomUImageName', 'ImageVersion', 'ntpServers']
        self.__net_dict = self.mGetNetworkDict(aConfig)

    def mGetNetworkById(self, aNetworkId):
        return self.__net_dict[aNetworkId]

    def mGetChildren(self, aXmlNode):
        _children = []
        try:
            _children = aXmlNode.getchildren()
        except AttributeError as e:
            _children = aXmlNode.findall("./")
        return _children

    def mGetMachineList(self, aConfig):
        _machine_list = []
        for _c1 in aConfig.mGetConfigAllElement('machines/machine'):
            _dict = {'id':_c1.attrib['id']}
            for _c2 in self.mGetChildren(_c1):
                #filter out attrs not on the list
                if _c2.tag not in self.__attr_list:
                    continue
                if _c2.tag == 'networks':
                    _networks = []
                    for _c3 in self.mGetChildren(_c2):
                        _networks.append(_c3.attrib['id'])
                    _dict['networks'] = _networks
                elif _c2.tag == 'machine':
                    #add sub list for vm - machines: ['id1', 'id2', ...]
                    if 'machines' not in _dict:
                        _dict['machines'] = []
                    _dict['machines'].append(_c2.attrib['id'])
                elif _c2.tag == 'ntpServers':
                    _ntpservers = []
                    for _c4 in _c2.findall('ntpServer/ipAddress'):
                        _ntpservers.append(_c4.text)
                    _dict['ntpServers'] = _ntpservers
                else:
                    _dict[_c2.tag] = _c2.text

            _machine_list.append(_dict)
        return _machine_list

    def mGetClusterList(self, aConfig):
        _clu_list = []
        _dg_dict = {}
        #prepare dg dict
        for _c1 in aConfig.mGetConfigAllElement('storage/diskGroups/diskGroup'):
            _cd = []
            for _c2 in _c1.findall('machines/machine'):
                _cd.append(_c2.attrib['id'])
            _dg_dict[_c1.attrib['id']] = _cd

        #build cluster list to return
        for _c1 in aConfig.mGetConfigAllElement('software/clusters/cluster'):
            _clu = {'id':_c1.attrib['id']}
            #build sub list - diskGroups
            _celldict = {}
            for _c2 in self.mGetChildren(_c1.find('diskGroups')):
                if _c2.attrib['id'] not in _dg_dict.keys():
                    print('Error - no dg info found. skipping...')
                    continue
                _celldict[_c2.attrib['id']]=_dg_dict[_c2.attrib['id']]
            _clu['diskGroups'] = _celldict

            #build sub list - machines(vm)
            _vmlist = []
            for _c2 in _c1.findall('clusterVips/clusterVip/machines/machine'):
                _vmlist.append(_c2.attrib['id'])
            _clu['machines'] = _vmlist

            #build vip list
            _viplist = []
            for _c2 in _c1.findall('clusterVips/clusterVip/vipName'):
                _viplist.append(_c2.text)
            _clu['vips'] = _viplist

            #build scan ip list
            _scanlist = []
            for _c2 in _c1.findall('clusterScans/clusterScan'):
                try:
                    _qstr = "software/clusters/clusterScans/clusterScan[@id='%s']/scanName" % _c2.attrib['id']
                    _cscan = aConfig.mGetConfigElement(_qstr)
                    _scanlist.append(_cscan.text)
                except:
                    print('cannot find scanName for ' + _c2.attrib['id'])
                    continue
            _clu['scanIps'] = _scanlist

            _clu_list.append(_clu)

        return _clu_list

    def mGetNetworkList(self):
        return self.__net_dict

    def mGetNetworkDict(self, aConfig):
        _net_dict = {}
        for _c1 in aConfig.mGetConfigAllElement('networks/network'):
            _dict = {'id' : _c1.attrib['id']}
            for _c2 in self.mGetChildren(_c1):
                _dict[_c2.tag] = _c2.text
            #handling cluster private case
            if _dict['networkType'] == 'private' and \
            'pkeyName' in _dict.keys() and _dict['pkeyName'][:2] == 'cl':
                _dict['networkType'] = 'clusterprivate'
            if _dict['networkType'] == 'Ilom':
                _dict['networkType'] = 'admin'
            _dict['shortHostName'] = _dict['hostName']
            _dict['hostName'] = '%s.%s' % (_dict['hostName'],
                                           _dict['domainName'])

            _net_dict[_c1.attrib['id']] = _dict
        return _net_dict

    def mGetCPConnTargetList(self, aConfig):
        _target_list = self.mGetMachineList(aConfig)
        def _mGetILOMs():
            _ILOM_list = []
            for _ILOM in aConfig.mGetConfigAllElement('iloms/ilom'):
                _dict = {'osType':'ilom', 'id':_ILOM.attrib['id'],
                         'networks':[_ILOM.attrib['id']]}
                _ILOM_list.append(_dict)
            return _ILOM_list

        def _mGetIbSwitches():
            _switch_list = []
            for _switchnet in aConfig.mGetConfigAllElement('.//switches/switch/ibPartitionMembership/../networks/network'):
                _dict = {'osType':'IbSwitch', 'id':_switchnet.attrib['id'],
                         'networks':[_switchnet.attrib['id']]}
                _switch_list.append(_dict)
            return _switch_list

        _target_list += _mGetIbSwitches()
        _target_list += _mGetILOMs()

        return _target_list

    def mGetSwitchList(self, aConfig):
        _switch_list = []
        for _c1 in aConfig.mGetConfigAllElement('.//switches/switch'):
            try:
                _d = {}
                for _c2 in self.mGetChildren(_c1):
                    _d[_c2.tag] = _c2.text
                _d.pop('networks')
                _d['network_id'] = _c1.find('networks/network').attrib['id']
                _switch_list.append(_d)
            except Exception as e:
                ebLogInfo(None, 'Invalid xml - failed to parse switches, error message: %s' % str(e))
        return _switch_list

    def mGetRackName(self, aConfig):
        return aConfig.mGetConfigAllElement('customerName').text

    def mGetDatabaseList(self, aConfig):
        _db_attr_list = ['databaseSid', 'databaseType']
        _db_list = []
        for _database in aConfig.mGetConfigAllElement('databases/database'):
            _db = {'id' : _database.attrib['id']}
            _vmlist = []
            for _machine in _database.findall('machines/machine'):
                _vmlist.append(_machine.attrib['id'])
            _db['machines'] = _vmlist
            for _child in self.mGetChildren(_database):
                if _child.tag in _db_attr_list:
                    _db[_child.tag] = _child.text
            _db_list.append(_db)
        return _db_list

class InterConnTarget(object):
    def __init__(self, aRemoteHost, aRemoteIp,
                 aRemoteMachineId, aNetType, aCheckList):
        self.remote_host = aRemoteHost
        self.remote_ip = aRemoteIp
        self.remote_machine_id = aRemoteMachineId
        self.nettype = aNetType
        self.checklist = aCheckList

class ebConnectivitylog(object):

    def __init__(self, aCluHealthCheck, aOptions):

        self.__hc = aCluHealthCheck
        self.__recommend = self.__hc.mGetRecommend()
        self.__jsonMap = self.__hc.mGetJsonMap()
        self.__loglist = []
        self.__testResult= "Pass"

    def mStartLog(self):
        self.__jsonMap['ConnectivityCheck'] = {}
        self.__jsonMap['ConnectivityCheck']['logs'] = {}
        self.__tmp_log_destination = ebLogSetHCLogDestination(self.__hc.mGetLogHandler(), True)

    def mAppendLog(self, aString, aFail=None):
        _fail   = aFail
        _log    = aString
        if(_fail == "Fail"):
            self.__recommend.append(_log)
            
            ebLogHealth('ERR', _log)
            self.__testResult = "Fail"
        self.__loglist.append(_log)
        ebLogHealth('NFO', _log)


    def mUpdateLog(self):
       
        print(len(self.__loglist))
        for i in range(len(self.__loglist)):
            self.__jsonMap['ConnectivityCheck']['logs'][i] = self.__loglist[i]
        
        self.__jsonMap['ConnectivityCheck']['TestResult'] = self.__testResult
        #clear loglist
        del self.__loglist[:]
        ebLogRemoveHCLogDestination(self.__tmp_log_destination)
        ebLogSetHCLogDestination(self.__hc.mGetDefaultLogHandler())

class ebCluConnectivityCheck(object):

    def __init__(self, aCluHealthCheck, aOptions):

        self.__hc = aCluHealthCheck
        self._prod_exacs = None
        self._thread_local = threading.local()
        self._thread_local.stopped_vm = []
        self._ecradb = None
        self.__provisioned = None
        self.__hcLog = ebConnectivitylog(aCluHealthCheck,aOptions)
        self.__hcLog.mStartLog()

        self.mSetProvisionStatus()

    
    def mAppendLog(self, aString, aFail=None):
        self.__hcLog.mAppendLog(aString, aFail)

    def mGetCluHealthCheck(self):
        return self.__hc

    def mSetProvisionStatus(self):
        #used same logic as healthcheck
        self.__provisioned = True
        if self.__hc.mGetPreProv() == 'True':
            self.__provisioned = False

    def mGetProvisionStatus(self):
        return self.__provisioned


    ##########################################copy code directly frm sanity check script##########################

    def get_interconnectivity_checklist(self, aFromMachine, aToMachine,
                                aNetworkName, aProvisioned):
        if aFromMachine == aToMachine:
            return False
        _from_type = aFromMachine['type']
        _to_type = aToMachine['type']
        _type_pair = [_from_type, _to_type]

        # for prod_exacs or ready rack, do not check interconnectivity from/to domU
        if 'domU' in _type_pair and (self._prod_exacs or not aProvisioned):
            return False

        # private networks are only used between cell-domU
        if aNetworkName == 'private':
            if _type_pair in (['cell', 'domU'], ['domU', 'cell']):
                # check if cell and domU are in a same cluster
                if _from_type == 'domU':
                    return (aFromMachine['cluster'] in aToMachine['clusters'])
                else:
                    return (aToMachine['cluster'] in aFromMachine['clusters'])
            elif _type_pair == ['cell', 'cell']:
                # do not check interconnectivity before provisioning
                if not aProvisioned:
                    return False
                # check if cells are in a same disk group - check intersection
                return bool(aFromMachine['clusters'] & aToMachine['clusters'])
            else:
                return False

        # do not check connectivity from IB switches (/etc/hostname not configured)
        if _from_type == 'IbSwitch':
            return False

        # check SSH between domUs in a same cluster over admin, client network
        if _type_pair == ['domU', 'domU']:
            if aFromMachine['cluster'] != aToMachine['cluster']:
                return False
            if aNetworkName in ['admin', 'client']:
                return {'ping' : True, 'ssh' : ['oracle', 'grid']}

        if aNetworkName == 'admin':
            # do not check domU interconnectivity (domU-domU will be checked)
            if 'domU' in _type_pair:
                return False
            # do not check ilom device connectivity
            if _to_type == 'ilom':
                return False

        # TODO: add more conditions
        return True


    def get_topology(self, aXmlMachines, aXmlClusters, aXmlNetworks, aProvisioned):
        _node_type_map = {'LinuxGuest': 'domU', 'LinuxDom0': 'dom0',
                            '_IbSwitch': 'ibs', 'LinuxPhysical': 'cell',
                            'ilom': 'ilom'}
        _nodes = []
        _networks = {}  # {network_type : [(hostname, ip, machine)]}
        _domU_clu_map = {} # {domU_id : cluster_id}
        _cell_clu_map = {} # {cell_id : {cluster_id}}
        _cell_dg_map = {} # {cell_id : {diskgroup_id}}
        _cluster_ips = {} # {cluster_id : [scan_ip + vip]}
        _machines = aXmlMachines
        
        # build _domU_clu_map, _cell_clu_map, _cell_dg_map
        for _cluster in aXmlClusters:
            for _machine in _cluster['machines']:
                _domU_clu_map[_machine] = _cluster['id']
            for _dg_id, _dg_cells in six.iteritems(_cluster['diskGroups']):
                for _cell in _dg_cells:
                    if _cell not in _cell_dg_map:
                        _cell_dg_map[_cell] = set()
                        _cell_clu_map[_cell] = set()
                    _cell_dg_map[_cell].add(_dg_id)
                    _cell_clu_map[_cell].add(_cluster['id'])
            _cluster_ips[_cluster['id']] = _cluster['scanIps'] + _cluster['vips']
            

        # add cluster information to machines
        for _machine in _machines:
            _machine['type'] = _node_type_map.get(_machine['osType'],
                                                    _machine['osType'])
            if _machine['type'] == 'dom0':
                _machine['clusters'] = set()
                for _vmid in _machine['machines']:
                    if _vmid in _domU_clu_map:
                        _machine['clusters'].add(_domU_clu_map[_vmid])
            elif _machine['type'] == 'domU':
                _machine['cluster'] = _domU_clu_map.get(_machine['id'], '')
            elif _machine['type'] == 'cell':
                _machine['clusters'] = _cell_clu_map.get(_machine['id'], set())
                _machine['diskgroups'] = _cell_dg_map.get(_machine['id'], set())

        # remove dom0s, domUs, cells which are not in target clusters
        def _is_machine_in_cluster(aMachine):
            if aMachine['type'] == 'domU':
                return aMachine.get('cluster')
            elif aMachine['type'] in ('dom0', 'cell'):
                return aMachine.get('clusters')
            return True

        _machines = [mac for mac in _machines if _is_machine_in_cluster(mac)]
        _machine_ids = set([mac['id'] for mac in _machines])

        # build _networks - {network_name : [(hostname, ip, machine), ], }
        # and set machine hostname
        for _machine in _machines:
            for _network_id in _machine['networks']:
                _network_info = aXmlNetworks[_network_id]
                _network = _networks.setdefault(_network_info['networkType'], [])
                _network.append((_network_info['hostName'],
                                    _network_info['ipAddress'], _machine))
                if _network_info['networkType'] == 'admin':
                    _machine['hostName'] = _network_info['hostName']

        def _add_connectable_host(aNode, aHost, aChkList=True,
                                    aIp='', aNetType='', aMacId=''):
            if aChkList:
                if aChkList == True: # allow True/False
                    aChkList = {'ping' : True}
                _target = InterConnTarget(aHost, aIp, aMacId, aNetType, aChkList)
                aNode['connectable_hosts'].append(_target)

        # build _nodes
        for _machine in _machines:
            _node = {}
            _node['type'] = _machine['type']
            _node['id'] = _machine['id']
            _node['hostname'] = _machine['hostName']
            _node['ntp_servers'] = _machine.get('ntpServers', [])
            _node['connectable_hosts'] = []
            _node['machines'] = []
            for _vm_id in _machine.get('machines', []):
                if _vm_id in _machine_ids:  # in cluster
                    _node['machines'].append(_vm_id)
            _node['networks'] = []
            _node['network_type'] = []
            for _network_id in _machine['networks']:
                _network_info = aXmlNetworks[_network_id]
                _network_type = _network_info['networkType']
                if _network_type not in _node['network_type']: # to avoid ib duplication
                    for _remotehostinfo in _networks[_network_type]:
                        _remotehost = _remotehostinfo[0]
                        _remoteip = _remotehostinfo[1]
                        _remotemachine = _remotehostinfo[2]
                        _chklist = self.get_interconnectivity_checklist(_machine,
                                                                    _remotemachine,
                                                                    _network_type,
                                                                    aProvisioned)
                        _add_connectable_host(_node, _remotehost, _chklist, _remoteip,
                                                _network_type, _remotemachine['id'])
                _node['networks'].append(_network_info)
                _node['network_type'].append(_network_type)
            if _node['type'] == 'domU':
                # check scan IPs and VIPs from domU
                for _vip_scan in _cluster_ips[_machine['cluster']]:
                    _add_connectable_host(_node, _vip_scan)
                # bug 26549230 ntp issue
                _add_connectable_host(_node, 'localhost')
            if 'DefaultGatewayNet' in _machine:
                _default_gw_net_id = _machine['DefaultGatewayNet']
                _default_gw_net = aXmlNetworks[_default_gw_net_id]
                _node['default_gateway'] = _default_gw_net['gateway']
            _nodes.append(_node)

        return _nodes

    def get_ip_status(self, aSSH):
        '''
        executes 'ip addr show' and returns a tuple
        ({ip : [netmask, if, state]}, [ifname, [flags], {property_name:value}])
        '''
        def _prefix_to_netmask(prefix):
            _mask = ~((1 << (32 - int(prefix))) - 1)
            return '%d.%d.%d.%d' % (((_mask >> 24) & 0xff), ((_mask >> 16) & 0xff),
                                    ((_mask >> 8) & 0xff), (_mask & 0xff))

        _i, _o, _e = aSSH.mExecuteCmd('ip addr show | grep "\(inet \|^[^ ]\)"')
        _interface = ''
        _state = False
        _ip_addresses = {}
        _interfaces = []
        for _line in _o:
            _words = _line.split()
            if _words[0] == 'inet':
                _ip, _prefix = _words[1].split('/')
                if _ip == '127.0.0.1':
                    continue
                _netmask = _prefix_to_netmask(_prefix)
                _interface = _words[-1] # TODO: need to check
                _ip_addresses[_ip] = (_netmask, _interface, _state)
            else:
                _if_name = _words[1][:-1]
                _flags = _words[2][1:-1].split(',')
                _properties = {}
                for i in range(3, len(_words), 2):
                    _properties[_words[i]] = _words[i+1]
                _interfaces.append([_if_name, _flags, _properties])
                _state = ('UP' in _flags)
        return _ip_addresses, _interfaces



    def check_network_addresses(self, aSSH, aNode):
        #_cmd = get_cmd('ip')
        def _interface_name(aXmlNetwork):
            if aNode['type'] == 'dom0' and aXmlNetwork['master'].startswith('eth'):
                return 'vm' + aXmlNetwork['master']
            if aXmlNetwork.get('pkeyName'):
                #return '%s@%s' % (aXmlNetwork['pkeyName'],
                #aXmlNetwork['master'])
                return aXmlNetwork['pkeyName']
            return aXmlNetwork['master']
        _current_addresses, _current_interfaces = self.get_ip_status(aSSH)
        _xml_ips = []
        _hostname = aNode['hostname']
        # check for eth links (IB link status will be checked later)
        for _intf_name, _intf_flags, _intf_properties in _current_interfaces:
            if _intf_name.startswith('eth'):
                if 'NO-CARRIER' in _intf_flags:
                    ebLogInfo('Network link','Host: %s, NO-CARRIER flag in "ip addr show %s"' % (_hostname, _intf_name))
                    ####print_csv(['LINK', 'ip_addr_show', 'FAIL', _hostname,_intf_name, 'NO-CARRIER'])
                    ###_cmd['fail'] += 1
                    self.mAppendLog('Network link: Host: %s, NO-CARRIER flag in "ip addr show %s"' % (_hostname, _intf_name), "Fail")
                else:
                    ebLogDebug('%s : %s does not have NO-CARRIER flag' % (_hostname, _intf_name))
                    self.mAppendLog('%s : %s does not have NO-CARRIER flag' % (_hostname, _intf_name))
                    ####print_csv(['LINK','ip_addr_show','SUC',_hostname,_intf_name])
                    ###_cmd['suc'] += 1
        # check ip addresses in xml
        for _xml_net in aNode['networks']:
            _xml_ip = _xml_net['ipAddress']
            _xml_ips.append(_xml_ip)
            _net_host = _xml_net['shortHostName']
            # do not check dom0 private network
            if aNode['type'] == 'dom0' and _xml_net['networkType'] == 'private':
                continue
            if _xml_ip not in _current_addresses:
                # TODO: VIP, SCAN IP (At this time domUs are not checked)
                ebLogInfo('Ip inconsistency', 'Host: %s, %s(%s) is in XML, but not set' % (_hostname, _xml_ip, _net_host))
                ####print_csv(['IP', 'ip_addr_show', 'FAIL', _hostname, _net_host,'Not set on machine'])
                ###_cmd['fail'] += 1
                self.mAppendLog('Ip inconsistency: Host: %s, %s(%s) is in XML, but not set' % (_hostname, _xml_ip, _net_host), "Fail")
                continue
            _cur_net = _current_addresses[_xml_ip]
            if _xml_net['netMask'] != _cur_net[0]:
                ebLogInfo('Netmask inconsistency', 'Host: %s, %s(%s) - XML is %s, but setup is %s' % (_hostname, _xml_ip, _net_host, 
                                _xml_net['netMask'], _cur_net[0]))
                ####print_csv(['NETMASK', 'ip_addr_show', 'FAIL', _hostname, _net_host,'XML %s, set %s' % (_xml_net['netMask'], _cur_net[0])])
                ###_cmd['fail'] += 1
                self.mAppendLog('Netmask inconsistency: Host: %s, %s(%s) - XML is %s, but setup is %s' % (_hostname, _xml_ip, _net_host, 
                                _xml_net['netMask'], _cur_net[0]), "Fail")
                continue
            _xml_interface = _interface_name(_xml_net)
            if (_xml_interface != _cur_net[1] and not (aNode['type'] == 'domU' and _xml_interface == 'eth0' and _cur_net[1] == 'eth1')):
                ebLogInfo('Net Interface inconsistency', 'Host: %s, %s(%s) should be on %s, but on %s' % (_hostname, _xml_ip, _net_host, _xml_interface,
                                _cur_net[1]))
                ####print_csv(['IP_IF', 'ip_addr_show', 'FAIL', _hostname, _net_host,'XML %s, set %s' % (_xml_interface, _cur_net[1])])
                ###_cmd['fail'] += 1
                self.mAppendLog('Net Interface inconsistency: Host: %s, %s(%s) should be on %s, but on %s' % (_hostname, _xml_ip, _net_host, _xml_interface,
                                _cur_net[1]), "Fail")
                continue
            if not _cur_net[2]: # state
                ebLogInfo('Net Interface down', 'Host: %s, interface %s for %s down' % (_hostname, _cur_net[1], _net_host))
                self.mAppendLog('Net Interface down', 'Host: %s, interface %s for %s down' % (_hostname, _cur_net[1], _net_host))
                ####print_csv(['IP', 'ip_addr_show', 'FAIL', _hostname, _net_host, 'Interface down'])
                ###_cmd['fail'] += 1
                continue
            ebLogDebug('%s : interface %s ip %s netmask %s ok' % (_hostname, _xml_interface, _xml_ip, _cur_net[0]))
            self.mAppendLog('%s : interface %s ip %s netmask %s ok' % (_hostname, _xml_interface, _xml_ip, _cur_net[0]))
            ####print_csv(['IP', 'ip_addr_show', 'SUC', _hostname, _net_host])
            ###_cmd['suc'] += 1
        # check if any unknown ip address exists
        if aNode['type'] != 'domU':
            for _ip in _current_addresses:
                if _ip not in _xml_ips:
                    _netmask, _interface, _state = _current_addresses[_ip]
                    if _state:
                        ebLogInfo('Ip inconsistency', 'Host: %s, %s/%s on %s is not found in XML' % (_hostname, _ip, _netmask, _interface))
                        self.mAppendLog('Ip inconsistency: Host: %s, %s/%s on %s is not found in XML' % (_hostname, _ip, _netmask, _interface), "Fail")
                        ####print_csv(['IP', 'ip_addr_show', 'FAIL',_hostname, _interface,'unknown IP %s netmask %s' % (_ip, _netmask)])
                        ###_cmd['fail'] += 1
        return



    def check_remote_connection(self, aSSH, aSourceType, aHost, aHostIp, aHostNettype,
                            aCheckList, aConnectedUser):
        # Cell does not usually have hostname-ip mapping.
        # As a result, cell->cell and cell->domu generate lots of errors.
        # Use IP, if source node is cell and target network type is private.
        # In result log and csv, use hostname as before.
        if aSourceType in ['cell', 'domU'] and \
                aHostNettype in ['private', 'clusterprivate']:
            _hostname_or_ip = aHostIp
            _dst_in_msg = '%s(%s)' % (aHostIp, aHost)
        else:
            _hostname_or_ip = aHost
            _dst_in_msg = aHost

        def _ssh_exec(command):
            _i, _o, _e = aSSH.mExecuteCmd(command)
            return aSSH.mGetCmdExitStatus(), _o.read(), _e.read()

        def _test_ssh_interconnectivity():
            _cmd = "timeout 3 sh -c 'ssh -o StrictHostKeyChecking=no " \
                   "-o BatchMode=yes -o UserKnownHostsFile=/dev/null " \
                   "%s date'" % _hostname_or_ip
            _rc, _output, _err = _ssh_exec(_cmd)
            if _rc == 124:
                return 'SSH timeout'
            elif _rc != 0:
                # merge multiline warning
                _errlines = []
                for _line in _err.splitlines():
                    if _line.startswith('@@@@@@@'):
                        continue
                    if _line.startswith('Warning: Permanently added '):
                        continue
                    _errlines.append(_line)
                _err = ' '.join(_err.splitlines())  # merge multiline warning
                return '%s SSH failed (%s)' % (aConnectedUser, ' '.join(_errlines))
            return ''

        if aConnectedUser == 'root':
            if aCheckList.get('ping'):
                for _ in range(2):  # retry 2 times
                    _cmd = '/bin/ping -c 1 -W 3 %s > /dev/null' % _hostname_or_ip
                    _ping_result, _, _errmsg = _ssh_exec(_cmd)
                    if type(_errmsg) is str:
                        _errmsg.strip()
                    if _ping_result == 0:
                        break
                    if _errmsg: # not a timeout issue - do not retry
                        ##print_csv(['NtoN','Ping','FAIL',aHost,                                   _dst_in_msg,_errmsg])
                        ebLogError('Ping failed', '%s -> %s, %s' %
                                    (aHost, _dst_in_msg, _errmsg))
                        return _errmsg
                if _ping_result != 0:
                    ##print_csv(['NtoN','Ping','FAIL',aHost,aHost])
                    if _ping_result == 1:
                        _errmsg = 'no response'
                    else:
                        _errmsg = 'exit code %d' % _ping_result
                    ebLogError('Ping failed', '%s -> %s, %s' %
                                (aHost, _dst_in_msg, _errmsg))
                    return 'ping failed'

            if aCheckList.get('listen_port'):
                _unreachable_ports = []
                for _port in aCheckList['listen_port']:
                    # _cmd = 'nc -z -w 3 %s %d' % (aHost, _port) # nc not installed
                    _cmd = ("timeout 3 sh -c 'cat < /dev/null > /dev/tcp/%s/%d'" %
                            (_hostname_or_ip, _port))
                    if _ssh_exec(_cmd)[0] != 0:
                        _unreachable_ports.append(str(_port))
                if _unreachable_ports:
                    ##print_csv(['NtoN','TCP','FAIL',aHost,aHost,                               ','.join(_unreachable_ports)])
                    ebLogError('TCP check failed', '%s -> %s, Ports:%s' %
                                (aHost, _dst_in_msg,
                                 ','.join(_unreachable_ports)))
                    return 'TCP failed : port %s' % (','.join(_unreachable_ports))
                ebLogDebug('TCP listen port checked : %s' %
                             aCheckList['listen_port'])

            if 'ssh' in aCheckList and aConnectedUser in aCheckList['ssh']:
                _err = _test_ssh_interconnectivity()
                if _err:
                    ##print_csv(['NtoN','SSH','FAIL',aHost,aHost,_err])
                    ebLogError('SSH failed', '%s -> %s, %s' %
                                (aHost, _dst_in_msg, _err))
                    return _err
                else:
                    ebLogDebug('SSH to %s@%s ok' % (aConnectedUser, aHost))

        else: # oracle, grid
            if 'ssh' in aCheckList and aConnectedUser in aCheckList['ssh']:
                _err = _test_ssh_interconnectivity()
                if _err:
                    ##print_csv(['NtoN','SSH','FAIL',aHost,aHost,_err])
                    ebLogError('SSH failed', '%s -> %s, %s' %
                                (aHost, _dst_in_msg, _err))
                    return _err
                else:
                    ebLogDebug('SSH to %s@%s ok' % (aConnectedUser, aHost))
            else:
                return 'skipped'

        return ''

    def check_route(self, aSSH, aNode):
        #get all routings
        #_cmd = get_cmd('gw')
        def _get_routes(aSSH):
            _i, _o, _e = aSSH.mExecuteCmd('ip route show table all')
            return _o
        #{"table name" : {}}
        _routes = []
        for _line in _get_routes(aSSH):
            _ls = _line.rstrip().split()
            #interested only in default routes
            if _ls[0] != 'default':
                continue
            _d = {'type':_ls[0], 'gw' : _ls[2], 'dev': _ls[4]}
            #detect route table
            if len(_ls) >= 7:
                _d['table'] = _ls[6]
            else:
                _d['table'] = 'main'

            _routes.append(_d)

        def _lookup_route(gw, table=None):
            for _rd in _routes:
                #TODO check main table duplicates in other table
                if table and table != _rd['table']:
                    continue
                if _rd['gw'] == gw:
                    return True

            return False

        #validate with xml value
        #route entry for gw check
        for _network in aNode['networks']:
            if 'gateway' not in _network:
                continue
            _xml_gw = _network['gateway']
            if _lookup_route(_xml_gw):
                ebLogDebug('Route entry check for host %s: %s' % (aNode['hostname'],_xml_gw))
                self.mAppendLog('Route entry check for host %s: %s' % (aNode['hostname'],_xml_gw))
                #print_csv(['GW','Route','SUC',aNode['hostname'],aNode['hostname'], _xml_gw])
                #_cmd['suc'] += 1
            else:
                ebLogError('Gateway not registered', 'Host: %s, Cannot find gateway %s from routes'
                            % (aNode['hostname'], _xml_gw))
                self.mAppendLog('Gateway not registered: Host: %s, Cannot find gateway %s from routes'
                            % (aNode['hostname'], _xml_gw), "Fail")
                #print_csv(['GW','Route','FAIL',aNode['hostname'],aNode['hostname'], _xml_gw])
                #_cmd['fail'] +=1
        #default gateway entry check
        if 'default_gateway' in aNode.keys():
            _defgw = aNode['default_gateway']
            if _lookup_route(_defgw, 'main'):
                ebLogDebug('Default Gateway for host %s: %s' % (aNode['hostname'],_defgw))
                self.mAppendLog('Default Gateway for host %s: %s' % (aNode['hostname'],_defgw))
                #print_csv(['GW','Default Route','SUC',aNode['hostname'],aNode['hostname'], _defgw])
                #_cmd['suc'] += 1
            else:
                ebLogError('Gateway not registered', 'Host: %s, No default gateway %s'
                            % (aNode['hostname'], _defgw))
                self.mAppendLog('Gateway not registered', 'Host: %s, No default gateway %s'
                            % (aNode['hostname'], _defgw))
                #print_csv(['GW','Default Route','FAIL',aNode['hostname'],aNode['hostname'], _defgw])
                #_cmd['fail'] += 1


        #validate connectivity
        #TODO
        return

    def check_chrony(self, aNode, aData):
        def _get_chronyc_results():
            _, _o, _e = aNode.mExecuteCmd('chronyc -n sources')
            _out = _o.read()
            _err = _e.read().strip()
            if _err and not _out:
                raise Exception(_err)
            elif aNode.mGetCmdExitStatus():
                raise Exception(_out.strip())
            _results = []
            for _line in _out.splitlines()[3:]:
                _result = {}
                _result['mode'] = _line[0]
                _result['state'] = _line[1]
                _result['server'] = _line.split(None, 2)[1]
                _results.append(_result)
            return _results

        _host = aData['hostname']
        _chronyc_results = None
        try:
            _chronyc_results = _get_chronyc_results()
        except Exception as _e:
            ebLogError('Chronyc results check error', 'chronyc sources execution failed on %s (%s)' % (_host, _e))

        if _chronyc_results != None:   # no exception
            _time_source = None
            for _result in _chronyc_results:
                if _result['mode'] in '^=' and _result['state'] == '*':
                    _time_source = _result['server']
            if _time_source:
                self.mAppendLog('%s chronyd is in sync with %s' %
                                (_host, _time_source))
            else:
                ebLogError('Chrony status error', 
                        '%s chronyd is not in sync with external source' % _host)
                self.mAppendLog('Chrony status error: %s Chronyc is not in sync with external source' % _host, "Fail")
                ebLogInfo(str(_chronyc_results))

    def check_ntp(self, aNode, aData):
        def _get_servers_in_ntp_conf():
            _, _o, _ = aNode.mExecuteCmd(
                        "grep ^server /etc/ntp.conf | awk '{print $2}'")
            return _o.read().splitlines()
        def _get_ntpq_results():
            _, _o, _e = aNode.mExecuteCmd('ntpq -pn')
            _out = _o.read()
            _err = _e.read().strip()
            if _err and not _out:
                raise Exception(_err)
            _results = []
            for _line in _out.splitlines()[2:]:
                _result = {}
                _result['tally'] = _line[0]
                _data = _line[1:].split()
                _result['remote'] = _data[0]
                _result['refid'] = _data[1]
                _results.append(_result)
            return _results

        #_cmd = get_cmd('ntp')
        _host = aData['hostname']
        if 0:
            _ntp_conf_servers = _get_servers_in_ntp_conf()
            if set(_ntp_conf_servers) != set(aData['ntp_servers']):
                ebLogError('NTP config inconsistency',
                            '%s /etc/ntp.conf has different servers from XML' % _host)
                self.mAppendLog('NTP config inconsistency: %s /etc/ntp.conf has different servers from XML' % _host, "Fail")
                #print_csv(['NTP', 'ntp.conf', 'FAIL', _host, 'ntp.conf',
                #           'XML %s - ntp.conf %s' % (' '.join(aNode['ntp_servers']),
                #                                     ' '.join(_ntp_conf_servers))])
                #_cmd['fail'] += 1
            else:
                ebLogDebug('%s /etc/ntp.conf has same servers with XML' % _host)
                self.mAppendLog('%s /etc/ntp.conf has same servers with XML' % _host)
                #print_csv(['NTP', 'ntp.conf', 'SUC', _host, 'ntp.conf'])
                #_cmd['suc'] += 1

        _ntpq_results = None
        try:
            _ntpq_results = _get_ntpq_results()
        except Exception as _e:
            if str(_e).endswith('ntpq: command not found'):
                ebLogInfo('ntpq is not installed')
                _ntpq_results = None
                self.check_chrony(aNode, aData)
            else:
                ebLogError('NTP status check error', 'ntpq execution failed on %s (%s)' % (_host, _e))
                self.mAppendLog('NTP status check error: ntpq execution failed on %s (%s)' % (_host, _e), "Fail")

        if _ntpq_results != None:   # no exception
            _valid = False
            for _result in _ntpq_results:
                if _result['tally'] == '*' and _result['refid'] != '.LOCL.':
                    ebLogDebug('%s ntpd is in sync with %s' %
                                (_host, _result['remote']))
                    self.mAppendLog('%s ntpd is in sync with %s' %
                                (_host, _result['remote']))
                    #print_csv(['NTP', 'ntpq', 'SUC', _host, _result['remote']])
                    #_cmd['suc'] += 1
                    _valid = True
                    break
            if not _valid:
                ebLogError('NTP status error', 
                            '%s ntpd is not in sync with external source' % _host)
                self.mAppendLog('NTP status error: %s ntpd is not in sync with external source' % _host, "Fail")
                ebLogDebug(str(_ntpq_results))
                #print_csv(['NTP', 'ntpq', 'FAIL', _host, 'ntpq'])
                #_cmd['fail'] += 1


    def check_interconnectivity(self, aSSH, aNode, aConnectedUser, aProvisioned):
        #_cmd = get_cmd('ic')
        _node_type = aNode['type']
        for _target in aNode['connectable_hosts']:
            if not _target.checklist:
                continue
            if _target.remote_machine_id in self._thread_local.stopped_vm:
                continue
            _err = self.check_remote_connection(aSSH, _node_type, _target.remote_host,
                                           _target.remote_ip, _target.nettype,
                                           _target.checklist, aConnectedUser)
            if _err == '':
                ebLogDebug('Connection OK : %s -> %s' %(aNode['hostname'], _target.remote_host))
                self.mAppendLog('Connection OK : %s -> %s' %(aNode['hostname'], _target.remote_host))
                ##print_csv(['NtoN','ALL','SUC',aNode['hostname'],                           _target.remote_host])
                #_cmd['suc'] += 1
            elif _err == 'skipped':
                pass
            else:
                #_cmd['fail'] += 1
                ebLogError('Connection Fail : %s -> %s' %(aNode['hostname'], _target.remote_host))
                self.mAppendLog('Connection Fail : %s -> %s' %(aNode['hostname'], _target.remote_host), "Fail")
                
        return

    def check_network(self, aNodes, aProvisioned):
        #_cmd = get_cmd('node')
        for _node in aNodes:
            #do not check domU in ready rack
            #but vm existence will be reported in check_vm_status
            if not aProvisioned and _node['type'] == 'domU':
                continue
            if _node['id'] in self._thread_local.stopped_vm:
                continue
            _host = _node['hostname']
            if not self.mGetCluHealthCheck().mGetEbox().mPingHost(_host):
                ebLogError('Ping failed', '%s -> %s'% (os.environ['HOSTNAME'],_host))
                self.mAppendLog('Ping failed: %s -> %s'% (os.environ['HOSTNAME'],_host), "Fail")
                ###print_csv(['1toN','Ping','FAIL',os.environ['HOSTNAME'],_host])
                ##_cmd['fail'] += 1
                continue

            # skip ssh test for ilom, vip, scan ip
            if _node['type'] in ['ilom', 'vip', 'scanip'] or \
                        (_node['type'] == 'domU' and self._prod_exacs):
                ebLogDebug('Ping OK : Control plane -> %s, skip ssh for %s' %(_host, _node['type']))
                self.mAppendLog('Ping OK : Control plane -> %s, skip ssh for %s' %(_host, _node['type']))
                ###print_csv(['1toN','Ping','SUC',os.environ['HOSTNAME'],_host,_node['type']])
                ##_cmd['suc'] += 1
                continue

            # TBD: when exacloud supports multiple users 
            #_users = ['root']
            #if _node['type'] == 'domU': #not prod_exacs(checked in the above block)
            #    _users += ['oracle', 'grid']

            #for _user in _users:
            #    try:
            #        _key_path = [
            #            #'%s/clusters/%s/keys' % 
            #            #    (_options.exacloud_home, get_clustername(aRackInfo)),
            #            '%s/clusters/oeda'%_options.exacloud_home, 
            #            './oeda'
            #        ]
            #        # Get keys in clusters directory
            #        _key_path_tmp = glob.glob('%s/clusters/*' % 
            #                                    _options.exacloud_home)
            #        for _path in _key_path_tmp:
            #            if os.path.basename(_path) == 'oeda' or \
            #               os.path.islink(_path):
            #                _key_path_tmp.remove(_path)

            #        _key_path += [os.path.join(_path, 'keys') for _path in _key_path_tmp]

            #        _ssh_conn = sshcli(_host, _user)
            #        _ssh_conn.mConnect(aKeyPath=_key_path)
            #    except Exception as e:
            #        ebLogDebug(traceback.format_exc())
            #        ebLogError('SSH failed', '%s -> %s@%s, %s' %
            #                    (os.environ['HOSTNAME'], _user, _host, e))
            #        ###print_csv(['1toN','SSH','FAIL',os.environ['HOSTNAME'],_host,
            #                    _user+':'+repr(e)])
            #        ##_cmd['fail'] += 1
            #        continue

            #used exacloud node connection instead
            _ssh_conn = exaBoxNode(get_gcontext())
            try:
                _ssh_conn.mConnectTimed(aHost=_host, aTimeout='10')
            except:
                ebLogError('*** failed to connect to: %s (pingable though)' % (_host))
                ebLogHealth('WRN','*** CheckInfo failed to connect to: %s (pingable though)' % (_host))
                continue
        
        
            _user = 'root'
            ebLogDebug('Connection OK : Control plane -> %s@%s' %(_user, _host))
            self.mAppendLog('Connection OK : Control plane -> %s@%s' %(_user, _host))
            ###print_csv(['1toN','SSH','SUC',os.environ['HOSTNAME'],_host,_user])
            ##_cmd['suc'] += 1
            
            self.check_interconnectivity(_ssh_conn, _node, _user, aProvisioned)

            if _user != 'root':
                # check only ping interconnectivity for oracle, grid user
                _ssh_conn.mDisconnect()
                continue

            self.check_network_addresses(_ssh_conn, _node)

            if _node['type'] == 'domU':
                self.check_ntp(_ssh_conn, _node)

            ##if _options.gw:
            self.check_route(_ssh_conn, _node)

            _ssh_conn.mDisconnect()
        return


    def mRunConnectivityCheck(self):
        
        try:
            _hc    = self.mGetCluHealthCheck()
            _ebox = _hc.mGetEbox()
            _eboxconfig = _ebox.mGetConfig()
            
        
            _xmlConfig = ebXmlConfig(_eboxconfig)
            _xml_machines = _xmlConfig.mGetCPConnTargetList(_eboxconfig)
            _xml_clusters = _xmlConfig.mGetClusterList(_eboxconfig)
            _xml_networks = _xmlConfig.mGetNetworkList()
            _xml_databases = _xmlConfig.mGetDatabaseList(_eboxconfig)
        
            aProvisioned = self.mGetProvisionStatus()
            _nodes = self.get_topology(_xml_machines, _xml_clusters, _xml_networks, aProvisioned)
            ###TODO consider xmlparser to be in _thread_local
            self.check_network(_nodes, aProvisioned)
        except Exception as e:
            ebLogError('*** Exception occured while running connectivity check ')
            ebLogError(traceback.format_exc())

        finally:
            self.__hcLog.mUpdateLog()
            
        return
