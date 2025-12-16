"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    cluconfig.py - config xml parsing

FUNCTION:
    Provide classes for xml parsing

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
       mpedapro 11/17/25 - Enh::38235082 xml patching changes for sriov
       pbellary 10/02/25 - Bug 38426506 - X11M-Z: CREATE VM CLUSTER FAILS CREATE VM CAUSED BY WRONG EXACLOUD/OEDA STEPS MAPPING
       ajayasin 05/13/25 - 37673251: log optimization
       pbellary 04/16/25 - Bug 37778364: CONFIGURE EXASCALE IS FAILING IN X11 ENV FOR EXTREME FLASH STORAGE TYPES
       pbellary 01/23/25 - Bug 37506231 - EXACALE:CLUSTER PROVISIONING FAILING DUE TO EDV SERVICES STARTUP FAILURE
       aararora 01/23/25 - Bug 37510360: Add ntp and dns information from
                           original xml
       scoral   14/11/24 - Bug 37284842: Fix mGetDiskSize to support ZDLRA
       aararora 08/29/24 - Bug 36998256: IPv6 fixes
       aararora 04/16/24 - ER 36485120: IPv6 support in exacloud
       pbellary 09/04/24 - Enh 36976333 - EXASCALE:ADD NODE CHANGES FOR EXASCALE CLUSTERS 
       jesandov 01/26/24 - 36228031: Initial support of ExaCC with ExaScale
       naps     06/13/23 - Bug 35495315 - retain pkey during xml patching.
       aararora 02/01/23 - Add objects for dr vips and dr scans
       rkhemcha 07/22/22 - 34394780 - Fix logical error in mGetNetLacp
       jesandov 04/27/22 - Backport jesandov_bug-34092494 from
                           st_ecs_21.3.1.2.0
       dekuckre 12/02/21 - 33294041 - restrict clustername to 11 char
       jlombera 10/11/21 - ENH 33304767: add MTU attribute to
                           ebCluNetworkConfig
       jesandov 03/02/21 - 33533527 - ADD NET VLAN NAT ID
       oespinos 05/21/20 - 31388372 - UPDATE CPS DNS ENTRIES FOR KVM IN
                           OCIEXACC
       seha     04/16/20 - 31180368 XML ilom version parsing error
       ndesanto 10/02/19 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
       oespinos 11/05/19 - Create file
"""

from __future__ import print_function

import re
import socket
import time
import uuid
import xml.etree.cElementTree as etree
import copy
import json
from typing import Optional

from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose,ebLogTrace

MAX_CLU_NAME_LEN = 11

class ebCluMachineConfig(object):

    def __init__(self, aMachineConfig):

        machine=aMachineConfig
        self.__config = aMachineConfig
        self.__MId = machine.get('id')
        self.__hostname = machine.find('hostName')
        self.__Type = machine.find('machineType')
        self.__subType = machine.find('machineSubType')
        self.__osType = machine.find('osType')
        self.__version = machine.find('version')
        if self.__osType.text == 'LinuxKVMGuest' or self.__osType.text == 'LinuxGuest':
            self.__guestCores = machine.find('guestCores')
            self.__guestMemory = machine.find('guestMemory')
            self.__guestLocalDiskSize = machine.find('guestLocalDiskSize')
        else:
            self.__guestCores = None
            self.__guestMemory = None
            self.__guestLocalDiskSize = None

        self.__virtual = machine.find('virtual')
        self.__vmSize  = machine.find('vmSizeName')
        if self.__vmSize is not None:
            self.__vmSize = self.__vmSize.get('id')
        self.__defaultgw = machine.find('DefaultGatewayNet')
        self.__networks = machine.findall('networks/network')
        self.__edvVolumes = machine.findall('edvVolumes/edvVolume')
        self.__vmImgName = machine.find('DomUImageName')
        self.__vmImgVersion = machine.find('ImageVersion')
        self.__net_id_list = []
        for net in self.__networks:
            self.__net_id_list.append(net.get('id'))
        self.__edv_id_list = []
        for edv in self.__edvVolumes:
            self.__edv_id_list.append(edv.get('id'))
        vms = machine.findall('machine')
        self.__vm_list = []
        for vm in vms:
            self.__vm_list.append(vm.get('id'))
        self.__timeZone = machine.find('TimeZone')
        self.__storage = machine.findall('storage/localDisks/localDisk')
        self.__localdisks = []
        for _disk in self.__storage:
            self.__localdisks.append(_disk.get('id'))
        self.__localdisksCount = len(self.__localdisks)
        self.__dnsServers = machine.findall('dnsServers/dnsServer')
        self.__ntpServers = machine.findall('ntpServers/ntpServer')
        self.__ntp_ip_list = []
        self.__dns_ip_list = []
        self.__iloms = machine.findall('iloms/ilom')
        self.__ilom_id_list = []
        for _ilom in self.__iloms:
            self.__ilom_id_list.append(_ilom.get('id'))

    def mGetVersion(self):
        return self.__version.text

    def mGetVersionNum(self):
        version = ''
        for c in self.__version.text:
            if c in '0123456789':
                version = version + c
        if version:
            version = int(version)
        else:
            version = 0
        return version

    def mGetGuestCores(self):
        if self.__guestCores is not None:
            return self.__guestCores.text
        else:
            return None

    def mGetGuestMemory(self):
        if self.__guestMemory is not None:
            return self.__guestMemory.text
        else:
            return None

    def mGetGuestLocalDiskSize(self):
        if self.__guestLocalDiskSize is not None:
            return self.__guestLocalDiskSize.text
        else:
            return None

    def mPatchDBHomeConfig(self, aDBName='cX_databaseHome'):

        _ndbh = etree.Element('databaseHome')
        _ndbh.set('id',aDBName)
        self.__config.find('software/databaseHomes').append(_ndbh)

    def mGetNtpServers(self):
        self.__ntp_ip_list = []
        for _ntp in self.__ntpServers:
            _ip = _ntp.find('ipAddress')
            if _ip is not None:
                if _ip.text is not None:
                    self.__ntp_ip_list.append(_ip.text)
                elif _ip.attrib.get('id') is not None:
                    self.__ntp_ip_list.append(_ip.attrib.get('id'))
        return self.__ntp_ip_list

    def mGetDnsServers(self):
        self.__dns_ip_list = []
        for _dns in self.__dnsServers:
            _ip = _dns.find('ipAddress')
            if _ip is not None:
                if _ip.text is not None:
                    self.__dns_ip_list.append(_ip.text)
                elif _ip.attrib.get('id') is not None:
                    self.__dns_ip_list.append(_ip.attrib.get('id'))
        return self.__dns_ip_list

    def mGetLocaldisksCount(self):
        return self.__localdisksCount

    def mGetMacId(self):
        return self.__MId

    def mGetMacHostName(self):
        return self.__hostname.text

    def mGetMacType(self):
        return self.__Type.text

    def mGetMacSubType(self):
        if self.__subType is not None:
            return self.__subType.text
        else:
            return 'Undefined'

    def mGetMacTimeZone(self):
        return self.__timeZone.text

    def mGetMacOsType(self):
        return self.__osType.text

    def mGetMacVirtual(self):
        return self.__virtual.text

    # TODO: Note this is a text element to fix
    def mGetMacVMSize(self):
        return self.__vmSize

    def mSetMacVMImgName(self, aVmImgName):
        self.__vmImgName.text = aVmImgName

    def mGetMacVMImgName(self):
        return self.__vmImgName.text

    def mSetMacVMImgVersion(self, aVmImgVersion):
        self.__vmImgVersion.text = aVmImgVersion

    def mGetMacVMImgVersion(self):
        return self.__vmImgVersion.text

    def mGetMacNetworks(self):
        return self.__net_id_list

    def mGetEdvVolumes(self):
        return self.__edv_id_list

    def mGetMacIlomNetworks(self):
        return self.__ilom_id_list

    def mGetMacMachines(self):
        return self.__vm_list

    def mGetMacGateWay(self):
        if self.__defaultgw:
            return self.__defaultgw.text
        else:
            return None
    #
    # Setters
    #
    def mSetMacHostName(self,aHostName):
        self.__hostname.text = aHostName

    def mSetMacType(self,aType):
        self.__Type=aType

    def mSetMacSubType(self, aSubType):
        if self.__subType:
            self.__subType.text = aSubType
        # Todo: if Element is not present create a new one.
        elt = etree.Element("machineSubType")
        elt.text = aSubType
        self.__config.append(elt)

    def mSetMacOsType(self, aOsType):
        self.__osType = aOsType

    def mSetMacGateWay(self,aGateWay):
        self.__defaultgw.text = aGateWay

    def mSetMacVirtual(self,aVirtual):
        self.__virtual = aVirtual

    def mSetmacVMSize(self, aVMSize):
        # Todo: Change attribute...
        raise ExacloudRuntimeError('TODO')

    def mSetMacNetworks(self, aNetworkList):
        raise ExacloudRuntimeError('TODO')

    def mSetMacMachines(self, aMachineList):
        raise ExacloudRuntimeError('TODO')

    def mSetMacTimeZone(self, aTimeZone):
        self.__timeZone.text = aTimeZone

    def mSetMacCores(self, aCores):
        if self.__guestCores is not None:
            self.__guestCores.text = aCores

    def mSetMacMemory(self, aMemory):
        if self.__guestMemory is not None:
            self.__guestMemory.text = aMemory

    def mSetMacDisk(self, aDisk):
        if self.__guestLocalDiskSize is not None:
            self.__guestLocalDiskSize.text = aDisk

    def mRemoveMacNetwork(self, aNetworkId):
        _network = None
        for net in self.__networks:
            if net.get('id') == aNetworkId:
                _network = net
        if _network is not None:
            self.__config.find('networks').remove(_network)
        else:
            ebLogWarn('Network Element not found: ' + aNetworkId)

    def mRemoveNtpServers(self):
        for _ntps in self.__ntpServers:
            self.__config.find('ntpServers').remove(_ntps)

    def mSetNtpServers(self,aNtpServersList):
        # Remove all NTP servers
        self.mRemoveNtpServers()
        # Add new list of NTP servers
        _ntpsl = aNtpServersList
        for _ip in _ntpsl:
            # Create ntpServer element
            _ntps = etree.Element('ntpServer')
            _ipaddr = etree.Element('ipAddress')
            _ipaddr.text = _ip
            _ntps.append(_ipaddr)
            self.__config.find('ntpServers').append(_ntps)

        # Repopulate ntpServers list
        self.__ntpServers = self.__config.findall('ntpServers/ntpServer')

    def mRemoveDnsServers(self):
        for _dnss in self.__dnsServers:
            self.__config.find('dnsServers').remove(_dnss)

    def mSetDnsServers(self,aDnsServersList):
        # Remove all DNS servers
        self.mRemoveDnsServers()
        # Add new list of DNS servers
        _dnssl = aDnsServersList
        for _ip in _dnssl:
            # Create dnsServer element
            _dnss = etree.Element('dnsServer')
            _ipaddr = etree.Element('ipAddress')
            _ipaddr.text = _ip
            _dnss.append(_ipaddr)
            self.__config.find('dnsServers').append(_dnss)

        # Repopulate dnsServers list
        self.__dnsServers = self.__config.findall('dnsServers/dnsServer')

    def mDumpConfig(self):

        _field_list = [ 'Id', 'HostName', 'Type', 'SubType', 'OsType', 'TimeZone', 'Virtual',
                'GateWay', 'VMSize', 'Networks', 'Machines',]

        _out = {}
        for field in _field_list:
            _method_string = "mGetMac{0}".format(field)
            _value = getattr(self, _method_string)()
            _out[field] = _value
        if _out:
            ebLogTrace(json.dumps(_out,indent=4))

    def mGetDict(self):
        _field_list = ['Id', 'HostName', 'Type', 'SubType', 'OsType', 'TimeZone', 'Virtual', 'GateWay', 'VMSize', 'Networks', 'Machines']
        _dict = {}

        for field in _field_list:
            _method_string = "mGetMac{0}".format(field)
            _value = getattr(self, _method_string)()
            _dict[field] = _value
        return _dict


class ebCluHeaderConfig(object):

    def __init__(self, aConfig):
        self.__engsys = aConfig.mConfigRoot()
        self.__filetype = self.__engsys.get('filetype')
        self.__oedaversion = self.__engsys.get('oedaversion')
        self.__customerName = aConfig.mGetConfigElement('customerName')
        self.__departmentName = aConfig.mGetConfigElement('departmentName')
        self.__esPrefix = aConfig.mGetConfigElement('esPrefix')
        self.__version = aConfig.mGetConfigElement('version')
        self.__skip_xml_signature = False

    def mGetHeaderFiletype(self):
        return self.__filetype

    def mGetRawOEDAVersion(self):
        return self.__oedaversion

    def mGetHeaderOEDAVersion(self):
        if not '.' in self.__oedaversion:
            _major = self.__oedaversion[:2]
            _minor = self.__oedaversion[2:]
        else:
            _major = self.__oedaversion.split('.')[0]
            _minor = self.__oedaversion.split('.')[1]
        return _major+'.'+_minor

    def mGetHeaderCustomerName(self):
        return self.__customerName.text

    def mGetHeaderDepartmentName(self):
        return self.__departmentName

    def mGetHeaderEsPrefix(self):
        return self.__esPrefix

    def mGetHeaderVersion(self):
        return self.__version

    def mGetXmlElasticShape(self):

        _xmlElasticShape = self.__engsys.find('XmlElasticShape')

        if _xmlElasticShape is not None:
            return _xmlElasticShape.text

        return ""

    def mGetSkipXmlSignature(self):
        return self.__skip_xml_signature

    def mSetSkipXmlSignature(self, aSkip):
        self.__skip_xml_signature = aSkip

    def mGenerateSignature(self, aCmd):
        if not self.__skip_xml_signature:
            self.__signature = self.__engsys.find('exacloud_signature')

            if self.__signature is None:
                self.__signature = etree.SubElement(self.__engsys, "exacloud_signature")

            #Generate the history
            _history = etree.SubElement(self.__signature, "history")
            etree.SubElement(_history, "last_update").text = time.strftime("%Y-%m-%d %H:%M:%S")
            etree.SubElement(_history, "exacloud_server").text = socket.getfqdn()
            etree.SubElement(_history, "exacloud_version").text = get_gcontext().mGetExacloudVersion()
            etree.SubElement(_history, "operation").text = aCmd

class ebCluMachinesConfig(object):

    def __init__(self, aConfig):

        self.__config = aConfig
        machines = aConfig.mGetConfigElement('machines')
        self.__mac_list = {}
        for machine in machines:
            mac = ebCluMachineConfig(machine)
            self.__mac_list[mac.mGetMacId()] = mac

    def mGetMachineConfig(self, aMachineId):
        if not aMachineId:
            return None
        try:
            return self.__mac_list[aMachineId]
        except:
            try:
                return self.__mac_list[aMachineId+'_id']
            except:
                #
                # If aMachineId does not end with _id
                # Go through all machine element and check if hostname matches.
                #
                if aMachineId[-3:] != '_id':
                    for _mac in list(self.__mac_list.keys()):
                        _mac_hostname = self.__mac_list[_mac].mGetMacHostName()
                        if  _mac_hostname == aMachineId:
                            return self.__mac_list[_mac]
                return None

    def mGetMachineConfigList(self):
        return self.__mac_list

    def mGetMacIdFromMacHostName(self, aHostName):
        for _mac_id in self.__mac_list:
            if aHostName == self.__mac_list[_mac_id].mGetMacHostName():
                if _mac_id.endswith("_id"):
                    return _mac_id[:-3]
                else:
                    return _mac_id.split('_')[0]
        return None


    def mRemoveMachinesConfig(self,aMachineList, aExactId=False):
        _machines = self.__config.mGetConfigElement('machines')
        for _machine in reversed(_machines):

            _toRemove = False

            if aExactId:
                if _machine.get('id') == aMachineList:
                    _toRemove = True
            else:
                if _machine.get('id').split('_')[0] in aMachineList:
                    _toRemove = True

            if _toRemove:
                ebLogInfo("removing machine %s from machines/machine" % (_machine.get('id')))
                _machines.remove(_machine)
                del self.__mac_list[_machine.get('id')]

    def mDumpConfig(self, aMachineId=None):

        if aMachineId:
            self.__mac_list[aMachineId].mDumpConfig()
        else:
            for _macid in list(self.__mac_list.keys()):
                self.__mac_list[_macid].mDumpConfig()

    def mAppendMachinesConfigV6(self, aClusterName, aNetDict):
      _network = etree.Element('network')
      _network_id =  "c" + aClusterName[-1:]+ "_" + aNetDict["domu_oracle_name"] + "_client_v6"
      _network.set('id', _network_id)
      _machines = self.__config.mGetConfigElement('machines')
      for _machine in _machines:
          if  aNetDict["domu_oracle_name"] in _machine.get('id'):
              _mach = 'machines' + '/' + _machine.get('id')[:-3] + '/' + 'networks'
              ebLogInfo("*** append machine %s from machines/machine " % (_machine.get('id')))
              _machine = _machine.find('networks').append(_network)

#
# DR VIP config
#
class ebCluDRVipConfig(object):

    def __init__(self):

        self.__vipName = None
        self.__vipDomainNane = None
        self.__vipAddr = None

    def mGetDRVIPName(self):
        return self.__vipName

    def mGetDRVIPAddr(self):
        return self.__vipAddr

    def mGetDRVIPDomainName(self):
        return self.__vipDomainNane

    def mSetDRVIPName(self, aHostName):
        self.__vipName = aHostName

    def mSetDRVIPAddr(self, aIP):
        self.__vipAddr = aIP

    def mSetDRVIPDomainName(self,aDomainName):
        self.__vipDomainNane =  aDomainName

#
# Cluster and VIP config
#
class ebCluVipConfig(object):

    def __init__(self, aVipXML):

        cvip = aVipXML
        self.__cvip = cvip
        self.__vipId = cvip.get('id')
        self.__vipName = cvip.find('vipName')
        self.__vipDomainNane = cvip.find('domainName')
        self.__vipAddr = cvip.find('vipIpAddress')
        machines = cvip.findall('machines/machine')
        self.__mac_list = []
        for mac in machines:
            self.__mac_list.append(mac.get('id'))

    def mGetCVipId(self):
        return self.__vipId

    def mGetCVIPName(self):
        return self.__vipName.text

    def mGetCVIPAddr(self):
        if self.__vipAddr is not None:
            return self.__vipAddr.text
        else:
            return None

    def mGetCVIPMachines(self):
        return self.__mac_list

    def mGetCVIPDomainName(self):
        return self.__vipDomainNane.text

    def mSetCVIPName(self, aHostName):
        self.__vipName.text = aHostName

    def mSetCVIPAddr(self, aIP):
        if self.__vipAddr is not None:
            self.__vipAddr.text = aIP
        else:
            vipAddr = etree.Element('vipIpAddress')
            vipAddr.text = aIP
            self.__vipAddr = vipAddr
            self.__cvip.append(vipAddr)

    def mSetCVIPDomainName(self,aDomainName):
        self.__vipDomainNane.text =  aDomainName

    def mDumpConfig(self):

        print('vip:', self.mGetCVipId(), self.mGetCVIPName(), self.mGetCVIPAddr())
        for mac in self.__mac_list:
            _macid = mac
            print('_macid:', _macid)

    def __lt__(self, other):
        return self.__vipId < other.__vipId

class ebCluClusterConfig(object):

    def __init__(self, aClusterXML):

        cluster = aClusterXML
        self.__config         = aClusterXML
        self.__cluster_id     = cluster.get('id')
        self.__clusterName    = cluster.find('clusterName')
        self.__clusterOwner   = cluster.find('clusterOwner')
        self.__clusterVersion = cluster.find('clusterVersion')
        self.__clusterHome    = cluster.find('clusterHome')
        self.__clusterAsmSS   = cluster.find('asmScopedSecurity')

        _cluDiskGroup = cluster.findall('diskGroups/diskGroup')
        self.__clusterDGroups = []
        for _cdg in _cluDiskGroup:
            self.__clusterDGroups.append(_cdg.get('id'))

        _cluScanGroup = cluster.findall('clusterScans/clusterScan')
        self.__clu_scans = []
        for _cscan in _cluScanGroup:
            self.__clu_scans.append(_cscan.get('id'))

        cluVips = cluster.findall('clusterVips/clusterVip')
        self.__clu_vips = {}
        self.__clu_v6_vips = {}
        for cvip in cluVips:
            cvipo = ebCluVipConfig(cvip)
            _vipID =  cvipo.mGetCVipId()
            self.__clu_vips[cvipo.mGetCVipId()] = cvipo

        _patches = cluster.findall('patches/patch')
        self.__gihome_patches = []
        for _p in _patches:
            self.__gihome_patches.append(_p)

    def mSetPatches(self, aPatchList):

        _patches = self.__config.find('patches')
        if _patches:
            self.__config.remove(_patches)

        _patches = etree.Element("patches")

        for _patchNum in aPatchList:

            _patch = etree.Element("patch")
            _patchNumber = etree.Element("patchNumber")
            _patchNumber.text = _patchNum

            _patch.append(_patchNumber)
            _patches.append(_patch)

        self.__config.append(_patches)


    def mSetCluVersion(self,aVersion):
        self.__clusterVersion.text = aVersion

    def mSetCluHome(self,aLocation):
        self.__clusterHome.text = aLocation

    def mGetCluHome(self):
        return self.__clusterHome.text
    
    def mRemoveClusterVip(self,aCluVip):

        for _cvip in self.__config.findall('clusterVips/clusterVip'):
            if aCluVip == _cvip.get('id'):
                self.__config.find('clusterVips').remove(_cvip)
                break
        del self.__clu_vips[aCluVip]

    def mRemoveDiskGroup(self,aDiskGroup):

        for _dg in self.__config.findall('diskGroups/diskGroup'):
            if aDiskGroup == _dg.get('id'):
                self.__config.find('diskGroups').remove(_dg)
                break
        self.__clusterDGroups.remove(aDiskGroup)

    def mGetCluId(self):
        return self.__cluster_id

    def mGetCluName(self):
        # restrict clustername (asm scopedsecurity) to 11 characters
        # (in accordance with cell requirements).
        return self.__clusterName.text

    def mSetCluName(self,aName, aPrefix="clu", aForce=False):
        if aForce:
            _name = aName
        else:
            # restrict clustername (asm scopedsecurity) to 11 characters 
            # with a letter in start (in accordance with cell and OEDA requirements).
            # For patched xmls which have clustername more than 11 chars, the last 3 chars will contain the deduced pkey. ( Note: pkey is calculated in mPatchClusterName )
            # Hence, Its very critical to retain those last 3 chars, which makes every clustername unique and also to avoid re-deducing clustername in mPatchClusterName for everytime !

            ebLogInfo(f'*** mSetCluName:Input  cluster name is: {aName}')
            _rem = MAX_CLU_NAME_LEN - len(aPrefix)                                                                                                                                                                     
            _name = aPrefix + aName[-_rem:]

            # Start with letters
            if not re.match("[a-zA-Z]", _name[0]):
                _name = "c" + _name[-10:]

            # Ends with letters or numbers
            if not re.match("[a-zA-Z0-9]", _name[-1]):
                _name = _name[:10] + "l"

        ebLogInfo(f'*** mSetCluName:Output cluster name is: {_name}')
        self.__clusterName.text = _name

    def mGetCluAsmScopedSecurity(self):
        if self.__clusterAsmSS is None:  
            return None  
        else:
            return self.__clusterAsmSS.text

    def mSetCluAsmScopedSecurity(self, aValue):
        if self.__clusterAsmSS is None:
            self.__clusterAsmSS = etree.Element('asmScopedSecurity')
            self.__config.append(self.__clusterAsmSS)
        self.__clusterAsmSS.text = aValue

    def mGetCluVersion(self):
        return self.__clusterVersion.text

    def mGetCluVips(self):
        return self.__clu_vips

    def mGetCluV6Vips(self):
        return self.__clu_v6_vips

    def mGetCluScans(self):
        return self.__clu_scans

    def mGetCluDiskGroups(self):
        return self.__clusterDGroups

    def mGetClusterOwner(self):
        return self.__clusterOwner.text

    def mRemoveCluDiskGroupConfig(self, aDg):

        if aDg not in self.__clusterDGroups:
            return

        _cluDiskGroups = self.__config.findall('diskGroups/diskGroup')
        _cdg = None

        for _cd in _cluDiskGroups:
            if _cd.get('id') == aDg:
                _cdg = _cd
                break

        if _cdg is None:
            return

        # Remove entry from the run-time cluster structure
        self.__clusterDGroups.remove(aDg)

        # Remove it from the XML file
        self.__config.find('diskGroups').remove(_cdg)

    def mAddCluDiskGroupConfig(self, aDg):

        if aDg in self.__clusterDGroups:
            return

        _cluDiskGroups = self.__config.find('diskGroups')
        _sparseDg = etree.Element('diskGroup')
        _sparseDg.set('id', aDg)

        _cluDiskGroups.append(_sparseDg)
        self.__clusterDGroups.append(aDg)

    def mDumpConfig(self):

        print('cluster:',self.mGetCluId(), self.mGetCluName(), self.mGetCluVersion())

        for vipId in list(self.__clu_vips.keys()):
            vip = self.__clu_vips[ vipId ]
            vip.mDumpConfig()

class ebCluDRScanConfig(object):

    def __init__(self):
        self.__scanPort = None
        self.__scanName = None
        self.__scan_ips = []

    def mGetScanPort(self):
        return self.__scanPort

    def mSetScanPort(self, aValue):
        if aValue:
            self.__scanPort = str(aValue)

    def mGetScanName(self):
        return self.__scanName

    def mSetScanName(self, aHostName):
        if aHostName:
            self.__scanName = aHostName

    def mSetScanIps(self, aScanIPs):
        if aScanIPs:
            self.__scan_ips = aScanIPs

    def mGetScanIpsList(self):
        return self.__scan_ips

class ebCluClusterScanConfig(object):

    def __init__(self,aClusterXML):

        _scan = aClusterXML
        self.__config      = aClusterXML
        self.__scan_id     = _scan.get('id')
        self.__scanName    = _scan.find('scanName')
        self.__scanType    = _scan.find('scanType')
        self.__scanPort    = _scan.find('scanPort')

        self.__scan_ips    = []

        _sips = _scan.findall('scanIps/scanIp')
        for _sip in _sips:
            self.__scan_ips.append(_sip.find('ipAddress'))

    def mGetScanPort(self):
        return self.__scanPort.text

    def mSetScanPort(self, aValue):
        self.__scanPort.text = str(aValue)

    def mGetScanName(self):
        return self.__scanName.text

    def mGetCluId(self):
        return self.__scan_id

    def mGetScanIps(self):
        _ips = []
        for _ipa in self.__scan_ips:
            _ips.append(_ipa.text)
        return _ips

    def mGetScanIpsList(self):
        return self.__scan_ips

    def mSetScanName(self, aHostName):
        self.__scanName.text = aHostName

class ebCluClusterScansConfig(object):

    def __init__(self, aConfig):

        _scans = aConfig.mGetConfigAllElement('software/clusters/clusterScans/clusterScan')
        self.__scans_list = {}

        for _scan in _scans:
            _scano = ebCluClusterScanConfig(_scan)
            self.__scans_list[_scano.mGetCluId()] = _scano

    def mGetScan(self, aScanId):
        return self.__scans_list[aScanId]

    def mGetScans(self):
        return list(self.__scans_list.keys())

    def mDumpConfig(self):
        for _key, _scan in list(self.__scans_list.items()):
            print(_key, _scan.mGetScanIps())

class ebCluClustersConfig(object):

    def __init__(self, aConfig, aOptions):

        clusters = aConfig.mGetConfigAllElement('software/clusters/cluster')
        self.__clusters = aConfig
        self.__clus_list = {}

        # MULTI-VM multi cluster section, consider only one cluster if
        # cluster_name in JSON
        _clu_filter = None
        _jconf = aOptions.jsonconf
        if _jconf is not None:
            _jconf_keys = list(_jconf.keys())
            if _jconf_keys is not None:
                if 'cluster_id' in _jconf_keys:
                    _clu_filter = _jconf['cluster_id']
                    ebLogInfo('*** MultiVM JSON payload with cluster_name specified: {}'.format(_clu_filter))

        # Multi-VM XML without cluster_id in JSON, default to c0 cluster
        if len(clusters) > 1 and not _clu_filter:
            for cluster in clusters:
                _clu_id = cluster.get('id')
                if 'C0' in _clu_id[:2].upper():
                    _clu_filter = _clu_id
                    break
            if not _clu_filter: #no clusters starts with c0, fallback to first
                _clu_filter = clusters[0].get('id')


        _clusterRoot = aConfig.mGetConfigElement('software/clusters')
        for cluster in clusters:
            if not _clu_filter:
                clu = ebCluClusterConfig(cluster)
                self.__clus_list[clu.mGetCluId()] = clu
            else:
                if _clu_filter.upper() == cluster.get('id').upper():
                    clu = ebCluClusterConfig(cluster)
                    self.__clus_list[clu.mGetCluId()] = clu
                else:
                    # Cluster Filter enabled and cluster name does not match
                    _clusterRoot.remove(cluster)


    def mDumpConfig(self):

        for clusterId in list(self.__clus_list.keys()):
            cluster = self.__clus_list[clusterId]
            cluster.mDumpConfig()

    def mGetClusters(self):
        return list(self.__clus_list.keys())

    def mGetCluster(self, aClusterId=None):

        # If aClusterId is not defined return the first cluster
        if not aClusterId:
            if not self.__clus_list.keys():
                return None
            clusterId = list(self.__clus_list.keys())[0]
        else:
            return self.__clus_list[aClusterId]

        return self.__clus_list[clusterId]

    def mGetClusterMachines(self, aClusterId=None):

        # If aClusterId is not defined return the first cluster
        if not aClusterId:
            if not self.__clus_list:
                return []
            clusterId = list(self.__clus_list.keys())[0]  # By default contains only entry corresponding to the cluster at hand
        else:
            clusterId = aClusterId

        cluster = self.__clus_list[clusterId]
        clu_vips = cluster.mGetCluVips()
        _macList = []
        for vip in list(clu_vips.keys()):
            mList = clu_vips[vip].mGetCVIPMachines()
            _macList = _macList + mList

        # There can be multiple VIPs for the same hostname
        return list(set(_macList))

    def mAppendClusterScanV6(self, aClusterName, aClusterScanDict):
        _clusterScan = etree.Element('clusterScan')
        _clusterScanName = "c" + aClusterName[-1:]+ "_" + "clusterScan_client" + '_v6'
        _clusterScan.set('id', _clusterScanName)
        etree.SubElement(_clusterScan, 'scanName').text = aClusterScanDict['hostname'] + '_v6'
        etree.SubElement(_clusterScan, 'scanType').text = 'v6_client'
        etree.SubElement(_clusterScan,'port').text = aClusterScanDict['port']
        _scanIps = etree.SubElement(_clusterScan,'scanIps')
        for _ip in aClusterScanDict['ips']:
            _scanIp = etree.SubElement(_scanIps,'scanIp')
            etree.SubElement(_scanIp,'ipAddress').text = _ip
        _clusterRoot = self.__clusters.mGetConfigElement('software/clusters/clusterScans')
        _clusterRoot.append(_clusterScan)

    def mAppendClusterVipV6(self, aClusterName, aClusterVipDict, domU):
       _clusterVips = etree.Element('clusterVips')
       _clusterVip = etree.SubElement(_clusterVips, 'clusterVip')
       _clusterVip_id = 'c' + aClusterName[-1:]+ '_' + domU.split('.')[0]  + '_vip_v6'
       _clusterVip.set('id', _clusterVip_id)
       etree.SubElement(_clusterVip, 'vipName').text = aClusterVipDict['hostname']
       etree.SubElement(_clusterVip, 'domainName').text = aClusterVipDict['domainname']
       etree.SubElement(_clusterVip, 'vipIpAddress').text = aClusterVipDict['ip']
       _machines = etree.SubElement(_clusterVip,'machines')
       _machine = etree.SubElement(_machines,'machine')
       _machine.set('id', domU +  '_id')
       _clusterRoot = self.__clusters.mGetConfigElement('software/clusters')
       _clu = 'c' + aClusterName[-1:] + '_clusterHome'
       for _cluster in _clusterRoot:
          if  _clu == _cluster.get('id'):
              _cluster.append(_clusterVips)
#
# DatabaseHomes Config
#

class ebDatabaseHomeConfig(object):

    def __init__(self, aDBId):

        self.db = etree.Element('databaseHome')
        _db = self.db
        _db.set('id',aDBId)
        self.__version = etree.SubElement(_db,'version')
        self.__cluster_id     = etree.SubElement(_db,'cluster')
        self.__dbhome_name    = etree.SubElement(_db,'databaseHomeName')
        self.__dbhome_owner   = etree.SubElement(_db,'databaseSwOwner')
        self.__dbhome_version = etree.SubElement(_db,'databaseVersion')
        self.__dbhome_location= etree.SubElement(_db,'databaseHomeLoc')
        self.__dbhome_lang    = etree.SubElement(_db,'language')

    def mGetDBHomeName(self):
        return self.__dbhome_name.text

class ebCluDatabaseHomeConfig(object):

    def __init__(self,aConfigXML):

        _dbhome = aConfigXML
        self.__config         = _dbhome
        self.__dbhome_id      = _dbhome.get('id')
        self.__dbhome_version = _dbhome.find('version')
        self.__cluster_id     = _dbhome.find('cluster').get('id')
        self.__dbhome_name    = _dbhome.find('databaseHomeName')
        self.__dbhome_owner   = _dbhome.find('databaseSwOwner')
        self.__dbhome_version = _dbhome.find('databaseVersion')
        self.__dbhome_location= _dbhome.find('databaseHomeLoc')
        self.__dbhome_lang    = _dbhome.find('language')

        _dbHomeMacs = _dbhome.findall('machines/machine')
        self.__dbhome_macs = []
        for _mac in _dbHomeMacs:
            self.__dbhome_macs.append(_mac.get('id'))

        _dbHomePatches = _dbhome.findall('patches/patch')
        self.__dbhome_patches = []
        for _patch in _dbHomePatches:
            self.__dbhome_patches.append(_patch)

    def mRemoveDBHomeMachine(self, aMachine):
        for _mac in self.__config.findall('machines/machine'):
            if _mac.get('id').startswith(aMachine):
                self.__config.find('machines').remove(_mac)
                self.__dbhome_macs.remove(_mac.get('id'))

    def mSetPatches(self, aPatchList):

        _patches = self.__config.find('patches')
        self.__config.remove(_patches)

        _patches = etree.Element("patches")

        for _patchNum in aPatchList:

            _patch = etree.Element("patch")
            _patchNumber = etree.Element("patchNumber")
            _patchNumber.text = _patchNum

            _patch.append(_patchNumber)
            _patches.append(_patch)

        self.__config.append(_patches)

    def mGetDBHomeConfig_ptr(self):
        return self.__config

    def mGetDBHomeId(self):
        return self.__dbhome_id

    def mGetDBClusterId(self):
        return self.__cluster_id

    def mGetDBHomeVersion(self):
        return self.__dbhome_version.text

    def mSetDBHomeVersion(self,aVersion):
        self.__dbhome_version.text = aVersion

    def mGetDBHomeLocation(self):
        return self.__dbhome_location.text

    def mSetDBHomeLocation(self,aLocation):
        self.__dbhome_location.text = aLocation

    def mGetDBHomeName(self):
        return self.__dbhome_name.text

    def mGetDBHomeLang(self):
        return self.__dbhome_lang.text

    def mGetDBHomeMacs(self):
        return self.__dbhome_macs

    def mSetDBHomeLang(self,aValue):
        self.__dbhome_lang.text = aValue

    def mGetDBHomeOwner(self):
        return self.__dbhome_owner.text

    def mDumpConfig(self):

        print(self.mGetDBHomeId())
        print(self.mGetDBHomeVersion())
        print(self.mGetDBHomeName())
        print(self.mGetDBHomeLang())
        print(self.mGetDBHomeLocation())

        for _mac in self.__dbhome_macs:
            print('\t',_mac)

class ebCluDatabaseHomesConfig(object):

    def __init__(self,aConfig):

        self.__config = aConfig
        _dbhomes = aConfig.mGetConfigAllElement('software/databaseHomes/databaseHome')
        self.__dbhomes_list = []

        for _dbhome in _dbhomes:
            _dbh = ebCluDatabaseHomeConfig(_dbhome)
            self.__dbhomes_list.append(_dbh)

    def mGetDBHomeConfigs_ptr(self):
        return self.__config.mGetConfigAllElement('software/databaseHomes/databaseHome')

    # TODO: Check that we pass a pointer to an XML element not the corresponding object
    def mAddNewDBHomeConfig(self,aDBHome):
        _dbh = ebCluDatabaseHomeConfig(aDBHome)
        self.__dbhomes_list.append(_dbh)
        self.__config.mGetConfigElement('software/databaseHomes').append(aDBHome)

    # TODO: Check that we pass a pointer to an XML element not the corresponding object
    def mRemoveDBHomeConfig(self,aDBHome, aObject=None):
        if aObject:
            self.__dbhomes_list.remove(aObject)
        self.__config.mConfigRoot().find('software/databaseHomes').remove(aDBHome)

    def mGetDBHomeConfigs(self):
        return self.__dbhomes_list

    def mGetDBHomeConfig(self,aDBHomeId):

        for _dbh in self.__dbhomes_list:
            if _dbh.mGetDBHomeId() == aDBHomeId:
                return _dbh
        return None

    def mDumpConfig(self):

        for _dbh in self.__dbhomes_list:
            _dbh.mDumpConfig()
#
# Database Config
#
class ebCluDatabaseConfig(object):

    def __init__(self, aDatabaseXML):

        db = aDatabaseXML
        self.__dbId = db.get('id')
        self.__dbowner = db.find('databaseOwner')
        self.__dbSid = db.find('databaseSid')
        self.__dbUnique = db.find('uniqueName')
        self.__dbBlkSize = db.find('databaseBlockSize')
        self.__dbHome = db.find('databaseHome')

        machines = db.findall('machines/machine')
        self.__mac_list = []
        for mac in machines:
            self.__mac_list.append(mac.get('id'))

        self.__dbtemplate = db.find('databaseTemplate')
        self.__dbstyle    = db.find('databaseStyle')
        self.__dblang     = db.find('language')

        # pdb, cdb or not set for regular db
        self.__dbtype     = db.find('databaseType')

        # for cdb type expect also cdbId
        self.__cdbid      = db.find('cdbId')

        dgroups = db.findall('diskGroups/diskGroup')
        self.__dg_list = []
        for dg in dgroups:
            self.__dg_list.append(dg.get('id'))

        self.__config = aDatabaseXML

    def mRemoveDBMachine(self, aMachine):
        for _mac in self.__config.findall('machines/machine'):
            if _mac.get('id').startswith(aMachine):
                self.__config.find('machines').remove(_mac)
                self.__mac_list.remove(_mac.get('id'))

    def mGetCDBid(self):
        if self.__cdbid == None:
            return None
        return self.__cdbid.text

    def mSetCDBid(self,aValue):
        self.__cdbid.text = aValue

    def mGetDBType(self):
        if self.__dbtype == None:
            return 'std'
        return self.__dbtype.text

    def mSetDBType(self,aValue):
        self.__dbtype = aValue

    def mRemoveDBType(self):
        _o = self.__config.find('databaseType')
        self.__config.remove(_o)

    def mGetDBId(self):
        return self.__dbId

    def mGetDBSid(self):
        return self.__dbSid.text

    def mGetDBBlkSize(self):
        return self.__dbBlkSize.text

    def mGetDBHome(self):
        return self.__dbHome.get('id')

    def mSetDBHome(self,aDBHomeId):
        self.__dbHome.set('id',aDBHomeId)

    def mGetDBMacs(self):
        return self.__mac_list

    def mGetDBDGs(self):
        return self.__dg_list

    def mGetDBTemplate(self):
        return self.__dbtemplate

    def mSetDBTemplate(self,aDBTemplate):
        self.__dbtemplate = aDBTemplate

    def mSetDBSid(self,aValue):
        self.__dbSid.text = aValue

    def mSetDBUnique(self,aValue):
        if self.__dbUnique is None:
            self.__dbUnique = etree.Element('uniqueName')
            self.__config.append(self.__dbUnique)
        self.__dbUnique.text = aValue


class ebCluDabasesConfig(object):

    def __init__(self, aConfig):

        databases = aConfig.mGetConfigAllElement('databases/database')
        self.__db_list = {}
        self.__db_list_o = {}
        self.__config = aConfig.mConfigRoot()

        for db in databases:
            dbo = ebCluDatabaseConfig(db)
            self.__db_list[dbo.mGetDBId()] = dbo
            self.__db_list_o[dbo.mGetDBId()] = db

    def mGetDBconfigs(self):
        return self.__db_list

    def mRemoveDatabaseConfig(self, aConfigId):

        if not aConfigId in list(self.__db_list.keys()):
            return

        _dbco = self.__db_list_o[aConfigId]
        del self.__db_list[aConfigId]
        del self.__db_list_o[aConfigId]
        _dbcl = self.__config.find('databases').remove(_dbco)
#
# Network Config
#
class ebCluNetworkConfig(object):

    def __init__(self, aNetworConfig):

        net = aNetworConfig
        self.__config = aNetworConfig
        self.__netId = net.get('id')
        self.__netName = net.find('networkName')
        self.__netType = net.find('networkType')
        self.__netVersion = net.find('version')
        self.__netHostName = net.find('hostName')
        self.__netIpAddr = net.find('ipAddress')
        self.__netNatHostName = net.find('nathostName')
        self.__netNatDomainName = net.find('natdomainName')
        self.__netNatAddr = net.find('natipAddress')
        self.__netNatMask = net.find('natnetMask')
        self.__macAddr   = net.find('macAddress')
        self.__vswitchNetworkParams = net.find('vswitchNetworkParams')
        aNetMask = net.find('netMask')
        if aNetMask and aNetMask.text.find('/') != -1:
            _netmask = aNetMask.text
            _netmask = _netmask[:_netmask.find('/')]
            ebLogDebug('*** NETMASK CORRECTED: %s - %s' % (aNetMask.text,_netmask))
            aNetMask.text = _netmask
        self.__netMask = aNetMask
        self.__domainName = net.find('domainName')
        self.__netGateWay = net.find('gateway')
        self.__netMaster = net.find('master')
        self.__netSlave = net.find('slave')
        self.__netVlanId = net.find('vlanId')
        self.__netVlanNatId = net.find('natVlanId')
        self.__netNatGateway = net.find('natGateway')
        self.__pkey = net.find('pkey')
        self.__pkeyName = net.find('pkeyName')
        self.__interfaceName = net.find('interfaceName')
        self.__netLacp = net.find('lacp')
        self.__netMtu = net.find('mtu')
        self.__acceleratedNetwork = net.find('acceleratedNetwork')
        #
        # Update Global NAT Lookup...
        #
        self.mUpdateNatLookup()

    def mUpdateNatLookup(self):
        _ctx = get_gcontext()
        if self.__netNatHostName is not None:
            _adminDM = self.__netNatDomainName.text
            _customerDM = self.__domainName.text
            _ctx.mSetRegEntry('_natHN_' + self.__netHostName.text + '.' + _customerDM, self.__netNatHostName.text + '.' + _adminDM)
            ebLogInfo('*** CTX_REG_NATHN %s : %s' % (
            '_natHN_' + self.__netHostName.text + '.' + _customerDM, self.__netNatHostName.text + '.' + _adminDM))
        if self.__netNatAddr is not None:
            _ctx.mSetRegEntry('_natIP_' + self.__netHostName.text, self.__netNatAddr.text)
            ebLogInfo('*** CTX_REG_NATIP %s : %s' % ('_natIP_' + self.__netHostName.text, self.__netNatAddr.text))

    def mGetPkey(self):
        if self.__pkey is None or self.__pkey.text is None:
            return 'UNDEFINED'
        else:
            return self.__pkey.text

    def mGetInterfaceName(self):
        if self.__interfaceName is None:
            return 'UNDEFINED'
        return self.__interfaceName.text

    def mGetPkeyName(self):
        if self.__pkeyName is None or self.__pkeyName.text is None:
            return 'UNDEFINED'
        else:
            return self.__pkeyName.text

    def mGetNetPkey(self):
        return self.mGetPkey()

    def mGetNetPkeyName(self):
        return self.mGetPkeyName()

    def mGetConfig(self):
        return self.__config

    def mGetNetId(self):
        return self.__config.get('id')

    def mGetNetName(self):
        return self.__netName.text

    def mGetNetType(self):
        return self.__netType.text

    def mGetNetVersion(self):
        return self.__netVersion.text

    def mGetNetHostName(self):
        return self.__netHostName.text

    def mGetNetDomainName(self):
        return self.__domainName.text

    def mGetNetIpAddr(self):
        return self.__netIpAddr.text

    def mGetNetNatHostName(self,aFallBack=True):
        if self.__netNatHostName is None and aFallBack is False:
            return None
        if self.__netNatHostName is None:
            return self.mGetNetHostName()
        return self.__netNatHostName.text

    def mGetNetNatDomainName(self):
        if self.__netNatDomainName is None:
            return self.mGetNetDomainName()
        return self.__netNatDomainName.text

    def mGetNetNatAddr(self, aFallBack=True, ip_version='4'):
        if self.__netNatAddr is None and aFallBack is False:
            return None
        if self.__netNatAddr is None:
            return self.mGetNetIpAddr()
        # NAT IP Address if present will be IPv4 only. NAT IP address will not be
        # present for IPv6
        if ip_version == '4':
            return self.__netNatAddr.text
        else:
            return None

    def mGetNetMacAddr(self):
        if self.__macAddr is None:
            return '00:00:00:00:00:00'
        return self.__macAddr.text

    def mGetNetVswitchNetworkParams(self):
        if self.__vswitchNetworkParams is None:
            return 'UNDEFINED'
        return self.__vswitchNetworkParams.text

    def mGetNetNatMask(self):
        if self.__netNatMask is None:
            return 'UNDEFINED'
        return self.__netNatMask.text

    def mGetNetMask(self):
        if self.__netMask is not None:
            return self.__netMask.text
        else:
            return None

    def mGetNetGateWay(self):
        if self.__netGateWay is not None:
            return self.__netGateWay.text
        else:
            return 'UNDEFINED'

    def mGetNetMaster(self):
        if self.__netMaster == None:
            return 'UNDEFINED'
        return self.__netMaster.text

    def mGetNetSlave(self):
        if self.__netSlave == None or self.__netSlave.text == None:
            return 'UNDEFINED'
        return self.__netSlave.text

    def mGetNetNatGateway(self):
        if self.__netNatGateway == None or self.__netNatGateway.text == None:
            return 'UNDEFINED'
        return self.__netNatGateway.text
    
    def mGetNetVlanId(self):
        if self.__netVlanId == None or self.__netVlanId.text == None:
            return 'UNDEFINED'
        return self.__netVlanId.text
    
    def mGetNetVlanNatId(self):
        if self.__netVlanNatId == None or self.__netVlanNatId.text == None:
            return 'UNDEFINED'
        return self.__netVlanNatId.text

    def mGetNetLacp(self) -> bool:
        return bool(self.__netLacp is not None and self.__netLacp.text.lower() == "true")

    def mGetNetMtu(self) -> Optional[int]:
        if self.__netMtu and self.__netMtu.text:
            return int(self.__netMtu.text)

        return None

    def mGetAcceleratedNetwork(self):
        if self.__acceleratedNetwork is None or self.__acceleratedNetwork.text is None:
            return 'UNDEFINED'
        return self.__acceleratedNetwork.text

    
    #
    # Setters
    #
    def mSetNetNatGateway(self,aNatGateway):
        if self.__netNatGateway is None:
            self.__netNatGateway = etree.Element('natGateway')
            self.__config.append(self.__netNatGateway)
        self.__netNatGateway.text = aNatGateway

    def mSetNetVlanId(self,aVlanId):
        if self.__netVlanId is None:
            self.__netVlanId = etree.Element('vlanId')
            self.__config.append(self.__netVlanId)
        self.__netVlanId.text = aVlanId

    def mSetNetVlanNatId(self,aVlanNatId):
        if self.__netVlanNatId is None:
            self.__netVlanNatId = etree.Element('natVlanId')
            self.__config.append(self.__netVlanNatId)
        self.__netVlanNatId.text = aVlanNatId

    def mSetNetId(self, aId):
        self.__config.set('id', aId)

    def mSetNetGateWay(self, aGateWay):
        if self.__netGateWay is not None:
            self.__netGateWay.text = aGateWay
        else:
            gateway = etree.Element('gateway')
            gateway.text = aGateWay
            self.__netGateWay = gateway
            self.__config.append(gateway)

    def mSetNetMaster(self, aMaster):
        self.__netMaster.text = aMaster

    def mSetNetIpAddr(self, aAddr):
        if self.__netIpAddr is not None:
            self.__netIpAddr.text = aAddr
        else:
            ip = etree.Element('ipAddress')
            ip.text = aAddr
            self.__netIpAddr = ip
            self.__config.append(ip)

    def mSetNetMask(self, aMask):
        if aMask.find('/') != -1:
            _netmask = aMask
            _netmask = _netmask[:_netmask.find('/')]
            ebLogDebug('*** NETMASK CORRECTED: %s - %s' % (aMask,_netmask))
            aMask = _netmask
        if self.__netMask is not None:
            self.__netMask.text = aMask
        else:
            netMask = etree.Element('netMask')
            netMask.text = aMask
            self.__netMask = netMask
            self.__config.append(netMask)

    def mSetNetHostName(self, aHostName):
        self.__netHostName.text = aHostName

    def mSetNetDomainName(self, aDomainName):
        self.__domainName.text = aDomainName

    def mSetNetSlave(self, aSlave):
        self.__netSlave.text = aSlave
    
    def mSetNetLacp(self, aValue: bool) -> None:
        if self.__netLacp is None:
            self.__netLacp = etree.Element('lacp')
            self.__config.append(self.__netLacp)

        self.__netLacp.text = "true" if aValue else "false"

    def mSetNetMtu(self, aValue: int) -> None:
        if self.__netMtu is None:
            self.__netMtu = etree.Element("mtu")
            self.__config.append(self.__netMtu)

        self.__netMtu.text = str(aValue)

    #
    # NAT/BM Setters
    #
    def mSetNatHostName(self, aHostName):
        self.__netNatHostName.text = aHostName

    def mSetNatDomainName(self, aDomainName):
        self.__netNatDomainName.text = aDomainName

    def mSetNatMask(self, aMask):
        if self.__netNatMask is None:
            self.__netNatMask = etree.Element('natnetMask')
            self.__config.append(self.__netNatMask)
        self.__netNatMask.text = aMask

    def mSetNatAddr(self, aAddr):
        self.__netNatAddr.text = aAddr

    def mSetMacAddr(self, aMac):
        self.__macAddr.text = aMac

    def mSetVswitchNetworkParams(self, aVswitchNetworkParams):
        self.__vswitchNetworkParams.text = aVswitchNetworkParams

    def mDumpConfig(self, aNetId=None):

        _field_list = [ 'Id', 'Name', 'Type', 'Version', 'HostName', 'IpAddr',\
                'Mask', 'GateWay', 'DomainName','Master', 'Slave', 'Pkey', 'PkeyName',\
                'NatHostName', 'NatAddr', 'MacAddr', 'NatMask', 'NatDomainName', 'VswitchNetworkParams']

        _out = {}
        for field in _field_list:
            _method_string = "mGetNet{0}".format(field)
            _value = getattr(self, _method_string)()
            _out[field] = _value
        if _out:
            ebLogTrace(json.dumps(_out,indent=4))

    def mDumpHostEntry(self):
        return self.mGetNetIpAddr()+' '+self.mGetNetHostName()+' '+self.mGetNetHostName()+'.'+self.mGetNetDomainName()


class ebCluNetworksConfig(object):

    def __init__(self, aConfig):

        networks = aConfig.mGetConfigElement('networks')
        self.__config = aConfig

        self.__net_list = {}

        for net in networks:
            neto = ebCluNetworkConfig(net)
            self.__net_list[neto.mGetNetId()] = neto

    def mDumpConfig(self):

        for netId in list(self.__net_list.keys()):
            net = self.__net_list[ netId ]
            net.mDumpConfig()

    def mDumpHostList(self):

        for netId in list(self.__net_list.keys()):
            net = self.__net_list[ netId ]
            ebLogInfo(net.mDumpHostEntry())

    def mGetNetworkConfig(self, aNetworkId):

         if aNetworkId in list(self.__net_list.keys()):
             return self.__net_list[aNetworkId]

    def mGetNetworkConfigByNatName(self, aHostname):
        for _key in self.__net_list.keys():
            _host = self.__net_list[ _key ].mGetNetNatHostName()
            _dom  = self.__net_list[ _key ].mGetNetNatDomainName()
            if aHostname == _host or (aHostname == _host+'.'+_dom):
                return self.__net_list[ _key ]

    def mGetNetworkConfigByName(self, aHostname):

        for _key in list(self.__net_list.keys()):
            _host = self.__net_list[ _key ].mGetNetHostName()
            _dom  = self.__net_list[ _key ].mGetNetDomainName()
            if aHostname == _host or (aHostname == _host+'.'+_dom):
                return self.__net_list[ _key ]

    def mDumpNetworkConfig(self, aNetworkId):

        if aNetworkId in list(self.__net_list.keys()):
             self.__net_list[aNetworkId].mDumpConfig()

    def mGetNetworkIdList(self):
        return list(self.__net_list.keys())

    def mRemoveNetworksConfig(self, aNetworkList):

        _networks = self.__config.mGetConfigElement('networks')
        for _net in reversed(_networks):
            _id = _net.get('id')
            if _id in aNetworkList:
                ebLogInfo("Removing network information %s from networks/network" % (_id))
                _networks.remove(_net)
                del self.__net_list[_id]

    def mSetNetworkConfigV6(self, aClusterName, aNetDict):
      _network = etree.Element('network')
      _network_id =  "c" + aClusterName[-1:]+ "_" + aNetDict["domu_oracle_name"] + "_client_v6"
      _network.set('id', _network_id)
      _networkName = etree.SubElement(_network, 'networkName').text = aNetDict['hostname'] + " Client"
      _networkType = etree.SubElement(_network, 'networkType').text = "client_v6"
      etree.SubElement(_network,'version').text = aNetDict['version']
      etree.SubElement(_network,'hostName').text = aNetDict['hostname']
      etree.SubElement(_network,'ipAddress').text = aNetDict['ip']
      etree.SubElement(_network,'gateway').text = aNetDict['gateway']
      etree.SubElement(_network,'netMask').text = aNetDict['netmask']
      etree.SubElement(_network,'domainName').text = aNetDict['domainname']
      etree.SubElement(_network,'master').text = 'bondeth0'
      etree.SubElement(_network,'slave').text = 'bondeth0'
      self.__config.mGetConfigElement('networks').append(_network)

class ebCluSwitchConfig(object):

    def __init__(self, aSwitchConfig):

        _swc = aSwitchConfig
        self.__config = aSwitchConfig
        self.__swId   = _swc.get('id')
        self.__swDesc = _swc.find('switchDescription')
        self.__swVer  = _swc.find('version')
        self.__swMShip= _swc.find('ibPartitionMembership')
        _net_conf = _swc.find('networks/network')
        if _net_conf is None:
            self.__swNetId = None
            ebLogWarn('*** Switch id: %s does not have valid network configuration' % (self.__swId))
        else:
            self.__swNetId = _net_conf.get('id')

    def mGetSwitchId(self):
        return self.__swId

    def mGetSwitchDesc(self):
        return self.__swDesc.text

    def mGetSwitchVer(self):
        return self.__swVer.text

    def mGetSwitchMemberShip(self):
        if self.__swMShip is None:
            return None
        else:
            return self.__swMShip.text

    def mGetSwitchNetworkId(self):
        return self.__swNetId

    def mDumpConfig(self):
        _swid   = self.mGetSwitchId()
        _swdesc = self.mGetSwitchDesc()
        _swver  = self.mGetSwitchVer()
        _swmship= self.mGetSwitchMemberShip()
        _swnetid= self.mGetSwitchNetworkId()
        ebLogInfo('*** Switch Config : %s %s %s %s %s' % (str(_swid), str(_swdesc), str(_swver), str(_swmship), str(_swnetid)))

    def mGetDict(self):
        _dict = {}
        _dict['swid']   = self.mGetSwitchId()
        _dict['swdesc'] = self.mGetSwitchDesc()

        try:
            _dict['swver']  = self.mGetSwitchVer()
        except:
            _dict['swver'] = "version1"

        try:
            _dict['swmship']= self.mGetSwitchMemberShip()
        except:
            pass

        _dict['swnetid']= self.mGetSwitchNetworkId()

        return _dict

class ebCluSwitchesConfig(object):

    def __init__(self, aConfig):

        _switches = aConfig.mGetConfigAllElement('switches/switch')
        _switches = [_switch for _switch in _switches if 'pdu' not in _switch.get('id')]
        self.__switches_list = {}

        for _sw in _switches:
            _swo = ebCluSwitchConfig(_sw)
            if _swo.mGetSwitchNetworkId() is not None:
                self.__switches_list[_swo.mGetSwitchId()] = _swo

    def mDumpConfig(self):

        for _swid in list(self.__switches_list.keys()):
            _swc = self.__switches_list[ _swid ]
            _swc.mDumpConfig()

    def mGetSwitchConfig(self, aSwitchId):

         if aSwitchId in list(self.__switches_list.keys()):
             return self.__switches_list[aSwitchId]

    def mGetSwitchesList(self):
        return list(self.__switches_list.keys())

    def mGetSwitchesDict(self, aFilter=False):

        _nid_list = []
        for _swid in list(self.__switches_list.keys()):
            _swc = self.__switches_list[ _swid ]
            if aFilter and _swc.mGetSwitchMemberShip() is None:
                continue
            _nid_list.append(_swc.mGetDict())

        return _nid_list

    def mGetSwitchesNetworkId(self,aFilter=False):

        _nid_list = []
        for _swid in list(self.__switches_list.keys()):
            _swc = self.__switches_list[ _swid ]
            if aFilter and _swc.mGetSwitchMemberShip() is None:
                continue
            _nid_list.append(_swc.mGetSwitchNetworkId())

        return _nid_list

class ebCluEsRackConfig(object):
    def __init__(self, aEsRackConfig):
        _esr = aEsRackConfig
        self.__config = aEsRackConfig
        self.__esrId = _esr.get('id')
        self.__esrType = _esr.find('rackType')
        self.__esrDesc = _esr.find('rackDescription')
        self.__esrUSize = _esr.find('rackUSize')
        self.__esrVer = _esr.find('version')

    def mGetEsRackId(self):
        return self.__esrId

    def mGetEsRackType(self):
        return self.__esrType

    def mGetEsRackDesc(self):
        return self.__esrDesc.text

    def mGetEsRackUSize(self):
        return self.__esrUSize

    def mGetEsRackVer(self):
        return self.__esrVer.text

    def mDumpConfig(self):
        _esrid = self.mGetEsRackId()
        _esrtype = self.mGetEsRackType()
        _esrdesc = self.mGetEsRackDesc()
        _esrusize = self.mGetEsRackUSize()
        _esrver = self.mGetEsRackVer()
        ebLogInfo('*** Rack Config : %s %s %s %s %s' % (
        str(_esrid), str(_esrtype), str(_esrdesc), str(_esrusize), str(_esrver)))

class ebCluEsRackItem(object):
    def __init__(self, aEsRackItem):
        _esr = aEsRackItem
        self.__config = aEsRackItem
        self.__esrId = _esr.get('id')
        self.__esrItemDesc = _esr.find('rackItemDescription')
        self.__esrItemFamily = _esr.find('rackItemFamily')
        self.__esrItemVer = _esr.find('version')

    def mGetEsRackItemId(self):
        return self.__esrId

    def mGetEsRackItemDesc(self):
        return self.__esrItemDesc.text

    def mGetEsRackItemFamily(self):
        return self.__esrItemFamily.text

    def mGetEsRackItemVer(self):
        return self.__esrItemVer.text

    def mDumpConfig(self):
        _esrid = self.mGetEsRackItemId()
        _esrdesc = self.mGetEsRackItemDesc()
        _esrfam = self.mGetEsRackItemFamily()
        _esrver = self.mGetEsRackItemVer()
        ebLogInfo('*** Rack Config : %s %s %s %s' % (
        str(_esrid), str(_esrdesc), str(_esrfam), str(_esrver)))

class ebCluEsRacksConfig(object):
    def __init__(self, aConfig):

        _esracks = aConfig.mGetConfigAllElement('esRacks/esRack')
        _esrackItems = aConfig.mGetConfigAllElement('esRacks/esRack/esRackItem')
        self.__esracks_list = {}
        self.__esrack_item_list = {}
        self.__disk_size = 0

        for esrack in _esracks:
            esro = ebCluEsRackConfig(esrack)
            self.__esracks_list[esro.mGetEsRackId()] = esro

        for esrackItem in _esrackItems:
            esro = ebCluEsRackItem(esrackItem)
            self.__esrack_item_list[esro.mGetEsRackItemId()] = esro

    def mGetEsRacksList(self):
        _list = []
        for esrack in self.__esracks_list:
            _list.append(esrack)
        return _list

    def mGetEsRackItemList(self):
        _list = []
        for esrack in self.__esrack_item_list:
            _list.append(esrack)
        return _list

    def mDumpConfig(self):

        for esrackId in list(self.__esracks_list.keys()):
            esrack = self.__esracks_list[esrackId]
            esrack.mDumpConfig()

        for esrackId in list(self.__esrack_item_list.keys()):
            esrack = self.__esrack_item_list[esrackId]
            esrack.mDumpConfig()

    def mGetEsRackConfig(self, aEsRackId):

        if aEsRackId in list(self.__esracks_list.keys()):
            return self.__esracks_list[aEsRackId]

    def mGetEsRackItem(self, aEsRackId):

        if aEsRackId in list(self.__esrack_item_list.keys()):
            return self.__esrack_item_list[aEsRackId]

    def mDumpEsRackDesc(self):

        _esr_desc_list = []
        for esrackId in list(self.__esracks_list.keys()):
            esrack = self.__esracks_list[esrackId]
            _esr_desc_list.append(esrack.mGetEsRackDesc())
        return _esr_desc_list[0]

    def mGetDiskSize(self):
        if self.__disk_size:
            return self.__disk_size
        _disk_rack = self.mDumpEsRackDesc().lower().split()
        self.__disk_size = int(''.join(filter(str.isdigit, _disk_rack[-1])))
        return self.__disk_size

    def mSetDiskSize(self, aSize):
        if type(aSize) == int:
            self.__disk_size = aSize


class ebCLuVMSizeConfig(object):

    def __init__(self, aConfig):

        self.__config = aConfig
        self.__vmAttrs = self.__config.findall('vmAttribute')
        self.__vmAttrsDict = {}
        for _vma in self.__vmAttrs:
             self.__vmAttrsDict[_vma.get('id')] = _vma

    def mGetVMSizeAttrKeys(self):
        return list(self.__vmAttrsDict.keys())

    def mGetVMSizeAttr(self, aKey):

        if aKey not in list(self.__vmAttrsDict.keys()):
            return None
        else:
            return self.__vmAttrsDict[aKey].text

    def mSetVMSizeAttr(self, aKey, aValue):

        if aKey not in list(self.__vmAttrsDict.keys()):
            return
        self.__vmAttrsDict[aKey].text = aValue

class ebCluVMSizesConfig(object):

    def __init__(self, aConfig):

        _vmSizeConfig = aConfig.mGetConfigAllElement('vmSizes/vmSizeName')
        self.__config = aConfig
        self.__vmSizes = {}
        for size in _vmSizeConfig:
            self.__vmSizes[size.get('id')] = [ size, ebCLuVMSizeConfig(size) ]

    def mGetVMSize(self, aVMId):

        if aVMId not in list(self.__vmSizes.keys()):
            return None
        else:
            return self.__vmSizes[aVMId][1]

class ebCluStorageDesc(object):

    def __init__(self, aConfig):

        _storageDesc = aConfig.mGetConfigAllElement('storageDesc/stAttribute')
        self.__config = aConfig
        self.__stAttributes = {}

        if _storageDesc == []:
            _sdElement = etree.Element('storageDesc')
            _saElement = etree.SubElement(_sdElement,'stAttribute')
            _saElement.set('id','TotalStorageSize')
            _saElement.text = 'Total_Storage_Size_Undefined'
            self.__config.mConfigRoot().insert(-1,_sdElement)
            _storageDesc = aConfig.mGetConfigAllElement('storageDesc/stAttribute')

        for _element in _storageDesc:
            self.__stAttributes[_element.get('id')] = [_element, _element.text]

    def mGetStorageDesc(self, aId):

        if aId not in list(self.__stAttributes.keys()):
            return None
        else:
            return self.__stAttributes[aId][1]

    def mSetStorageDesc(self, aId, aValue):
        if aId not in list(self.__stAttributes.keys()):
            ebLogWarn('*** ST_DESC Attributes setting not supported if not already present')
            return
        else:
            self.__stAttributes[aId][0].text = aValue
            self.__stAttributes[aId][1] = aValue
#
# Users Config
#
class ebCluUsersConfig(object):

        def __init__(self, aConfig):

            self.__users = aConfig.mGetConfigAllElement('users/user')
            self.__config = aConfig
            self.__users_list = {}

            for _user in self.__users:
                _usero = ebCluUserConfig(_user)
                self.__users_list[_usero.mGetUserConfigId()] = _usero

        def mCreateNewUser(self, aUserId, aName, aGroupId):

            # Clone exising group
            new_user = copy.deepcopy(self.__users[0])
            new_user.find("userid").text =  str(aUserId)
            new_user.find("username").text =  str(aName)
            new_user.find("userType").text =  str(aName).upper()
            new_user.find("homedir").text =  f"/home/{aName}"
            new_user.set('id', str(uuid.uuid1()))

            c = 0
            for _group in list(new_user.find("groups")):
                if c == 0:
                    _group.set('id', aGroupId)
                else:
                    new_user.find("groups").remove(_group)
                c += 1

            # Add group to XML
            self.__config.mGetConfigAllElement('users')[0].append(new_user)
            self.__users = self.__config.mGetConfigAllElement('users/user')
            for _user in self.__users:
                _usero = ebCluUserConfig(_user)
                self.__users_list[_usero.mGetUserConfigId()] = _usero

        def mGetUsers(self):
            return list(self.__users_list.keys())

        def mGetUserByName(self, aUsername):

            for _ucId in list(self.__users_list.keys()):

                _user = self.__users_list[_ucId]

                if _user.mGetUserName() == aUsername:
                    return _user

            return None

        def mGetUser(self, aUserId=None):

            # If aClusterId is not defined return the first cluster
            if not aUserId:
                _ucId = list(self.__users_list.keys())[0]
            else:
                return self.__users_list[aUserId]

            return self.__users_list[_ucId]

        def mDumpUserList(self):

            for _ucId in list(self.__users_list.keys()):
                _user = self.__users_list[_ucId]
                ebLogInfo('user name listed in XML file is %s' %(_user.mGetUserName()))


class ebCluUserConfig(object):

    def __init__(self, aUserConfig):

        user = aUserConfig
        self.__config = aUserConfig
        self._ucId = user.get('id')
        self.__userType = user.find('userType')
        self.__userName = user.find('username')
        self.__homeDir = user.find('homedir')
        self.__userId = user.find('userid')

        groups = user.findall('groups/group')
        self.__group_list = []
        for grp in groups:
            self.__group_list.append(grp.get('id'))

    def mGetConfig(self):
        return self.__config

    def mGetUserConfigId(self):
        return self.__config.get('id')

    def mGetUserType(self):
        return self.__userType.text

    def mGetUserName(self):
        return self.__userName.text

    def mGetHomeDir(self):
        return self.__homeDir.text

    def mGetUserId(self):
        return self.__userId.text

    def mSetUserId(self, aValue):
        self.__userId.text = aValue

    def mGetUserGroups(self):
        return self.__group_list

    def mDumpConfig(self):
        print('user:',self.mGetUserConfigId(), self.mGetUserName(), self.mGetUserType(), self.mGetHomeDir())
        for _groupId in self.__group_list:
            print(_groupId)

#
# Group Config
#

class ebCluGroupsConfig(object):

        def __init__(self, aConfig):

            self.__groups = aConfig.mGetConfigAllElement('groups/group')
            self.__groups_list = {}
            self.__config = aConfig

            for _group in self.__groups:
                _groupo = ebCluGroupConfig(_group)
                self.__groups_list[_groupo.mGetGroupConfigId()] = _groupo

        def mCreateNewGroup(self, aGroupId, aName):

            # Clone existing group
            new_group = copy.deepcopy(self.__groups[0])
            new_group.find("groupId").text =  str(aGroupId)
            new_group.find("groupName").text =  str(aName)
            new_group.find("groupType").text =  str(aName).upper()
            new_group.set('id', str(uuid.uuid1()))

            # Add to XML
            self.__config.mGetConfigAllElement('groups')[0].append(new_group)
            self.__groups = self.__config.mGetConfigAllElement('groups/group')
            for _group in self.__groups:
                _groupo = ebCluGroupConfig(_group)
                self.__groups_list[_groupo.mGetGroupConfigId()] = _groupo


        def mGetGroups(self):
            return list(self.__groups_list.keys())

        def mGetGroup(self, aGroupId=None):

            # If aClusterId is not defined return the first cluster
            if not aGroupId:
                groupId = list(self.__groups_list.keys())[0]
            else:
                return self.__groups_list[aGroupId]

            return self.__groups_list[groupId]

        def mGetGroupByName(self, aGroupName):

            for _groupId in list(self.__groups_list.keys()):
                _group = self.__groups_list[_groupId]

                if _group.mGetGroupName() == aGroupName:
                    return _group

            return None

        def mDumpGroupList(self):
            for _groupId in list(self.__groups_list.keys()):
                _group = self.__groups_list[_groupId]
                ebLogInfo('user name listed in XML file is %s' %(_group.mGetGroupName()))

class ebCluGroupConfig(object):

    def __init__(self, aGroupConfig):

        group = aGroupConfig
        self.__config = aGroupConfig
        self.__gcId = group.get('id')
        self.__groupType = group.find('groupType')
        self.__groupName = group.find('groupName')
        self.__groupId = group.find('groupId')

    def mGetConfig(self):
        return self.__config

    def mGetGroupConfigId(self):
        return self.__config.get('id')

    def mGetGroupType(self):
        return self.__groupType.text

    def mGetGroupName(self):
        return self.__groupName.text

    def mGetGroupId(self):
        return self.__groupId.text

    def mSetGroupId(self, aValue):
        self.__groupId.text = aValue

    def mDumpConfig(self):
        print('group:', self.mGetGroupConfigId(), self.mGetGroupName(), self.mGetGroupType(), self.mGetGroupId())

#
# Ilom Config
#
class ebCluIlomsConfig(object):

    def __init__(self, aConfig):
        self.__config = aConfig

        _iloms = aConfig.mGetConfigElement('iloms')
        self.__iloms_list = {}
        for _ilom in _iloms:
            _ilomo = ebCluIlomConfig(_ilom)
            _ilomo_id = _ilomo.mGetIlomId()
            if _ilomo_id:
                self.__iloms_list[_ilomo_id] = _ilomo

    def mGetIlomConfig(self, aIlomId):
         if aIlomId in list(self.__iloms_list.keys()):
             return self.__iloms_list[aIlomId]

    def mGetIlomsList(self):
        return list(self.__iloms_list.keys())

    def mGetIlomsNetworkId(self):
        _nid_list = []
        for _ilomId in list(self.__iloms_list.keys()):
            _ilomCfg = self.__iloms_list[_ilomId]
            _nid_list.append(_ilomCfg.mGetIlomNetworkId())
        return _nid_list

    def mDumpConfig(self):
        for _ilomId in list(self.__iloms_list.keys()):
            _ilom = self.__iloms_list[_ilomId]
            _ilom.mDumpConfig()

    def mRemoveIlomsConfig(self, aIlomList):

        _iloms = self.__config.mGetConfigElement('iloms')

        for _ilom in reversed(_iloms):
            _id = _ilom.get('id')
            if _id in aIlomList:
                ebLogInfo("Removing ilom information %s from iloms/ilom" % (_id))
                _iloms.remove(_ilom)
                del self.__iloms_list[_id]

class ebCluIlomConfig(object):

    def __init__(self, aIlomConfig):

        _ilomCfg = aIlomConfig
        self.__config       = aIlomConfig
        self._ilomId        = _ilomCfg.get('id')
        self._ilomName      = _ilomCfg.find('ilomName')
        self._ilomVer       = _ilomCfg.find('version')
        self._ilomTimeZone  = _ilomCfg.find('ilomTimeZone')
        _net_conf           = _ilomCfg.find('networks/network')
        self.__dnsServers   = _ilomCfg.findall('dnsServers/dnsServer')
        self.__ntpServers   = _ilomCfg.findall('ntpServers/ntpServer')

        if _net_conf is None:
            self._ilomNetId = None
            ebLogWarn('*** Ilom id: %s does not have valid network configuration' % (self._ilomId))
        else:
            self._ilomNetId = _net_conf.get('id')

    def mGetDict(self):
        _dict = {}
        _dict['ilomid']    = self.mGetIlomId()
        _dict['ilomname']  = self.mGetIlomName()
        _dict['ilomver']   = self.mGetIlomVer()
        _dict['ilomtz']    = self.mGetIlomTimeZone()
        _dict['ilomnetid'] = self.mGetIlomNetworkId()

        _dict['dns_ip'] = self.mGetDnsServers()
        _dict['ntp_ip'] = self.mGetNtpServers()
        return _dict

    def mGetNtpServers(self):
        self.__ntp_ip_list = []
        for _ntp in self.__ntpServers:
            _ip = _ntp.find('ipAddress')
            if _ip is not None:
                if _ip.text is not None:
                    self.__ntp_ip_list.append(_ip.text)
                elif _ip.attrib.get('id') is not None:
                    self.__ntp_ip_list.append(_ip.attrib.get('id'))
        return self.__ntp_ip_list

    def mGetDnsServers(self):
        self.__dns_ip_list = []
        dns = self.__dnsServers
        for _dns in dns:
            _ip = _dns.find('ipAddress')
            if _ip is not None:
                if _ip.text is not None:
                    self.__dns_ip_list.append(_ip.text)
                elif _ip.attrib.get('id') is not None:
                    self.__dns_ip_list.append(_ip.attrib.get('id'))
        return self.__dns_ip_list

    def mGetIlomId(self):
        return self._ilomId

    def mGetIlomName(self):
        return self._ilomName.text

    def mGetIlomVer(self):
        return self._ilomVer.text

    def mGetIlomTimeZone(self):
        if self._ilomTimeZone is None:
            return None
        else:
            return self._ilomTimeZone.text

    def mGetIlomNetworkId(self):
        return self._ilomNetId

    def mDumpConfig(self):

        _ilomid   = self.mGetIlomId()
        _ilomname = self.mGetIlomName()
        _ilomver  = self.mGetIlomVer()
        _ilomtz= self.mGetIlomTimeZone()
        _ilomnetid= self.mGetIlomNetworkId()

        ebLogInfo('*** Ilom Config \nid: %s name: %s  version: %s timezone: %s net id: %s'
                  %(str(_ilomid), str(_ilomname), str(_ilomver), str(_ilomtz), str(_ilomnetid)))
        for _dns_ip in self.mGetDnsServers():
            ebLogInfo('*** Ilom Dns Server Ip: %s' %(_dns_ip))
        for _ntp_ip in self.mGetNtpServers():
            ebLogInfo('*** Ilom Ntp Server Ip: %s' %(_ntp_ip))

class ebCluExascaleClustersConfig(object):

    def __init__(self, aConfig):
        config=aConfig
        self.__config = aConfig
        self.__exascaleClusterId = config.get('id')
        self.__clusterName = ""
        _name = config.find('clusterName')
        if _name is not None:
            self.__clusterName = _name.text
        self.__networks = config.findall('networks/network')
        self.__net_id_list = []
        for net in self.__networks:
            self.__net_id_list.append(net.get('id'))

    def mGetExascaleClusterId(self):
        return self.__exascaleClusterId

    def mGetClusterName(self):
        return self.__clusterName

    def mGetMacNetworks(self):
        return self.__net_id_list

class ebCluVaultConfig(object):

    def __init__(self, aConfig):
        config=aConfig
        self.__config = aConfig
        self.__vaultId = config.get('id')
        name = config.find('name')
        if name is not None:
            self.__vaultName = name.text

    def mGetVaultName(self):
        return self.__vaultName

    def mGetVaultId(self):
        return self.__vaultId

class ebCluExascaleConfig(object):
    def __init__(self, aConfig):
        _exascaleClusters = aConfig.mGetConfigAllElement('exascale/exascaleClusters/exascaleCluster')
        _vaults = aConfig.mGetConfigAllElement('exascale/vaults/vault')

        self.__exaconfig_list = {}
        for _exascaleCluster in _exascaleClusters:
            _clusterConfig = ebCluExascaleClustersConfig(_exascaleCluster)
            self.__exaconfig_list[_clusterConfig.mGetExascaleClusterId()] = _clusterConfig

        self.__vaultconfig_list = {}
        for _vault in _vaults:
            _vaultConfig = ebCluVaultConfig(_vault)
            self.__vaultconfig_list[_vaultConfig.mGetVaultId()] = _vaultConfig

        self.__config = aConfig.mConfigRoot()

    def mGetExascaleClusterConfigList(self):
        return list(self.__exaconfig_list.keys())

    def mGetExascaleClusterConfig(self, aVaultId):
        return self.__exaconfig_list[aVaultId]

    def mGetVaultConfigList(self):
        return list(self.__vaultconfig_list.keys())

    def mGetVaultConfig(self, aVaultId):
        return self.__vaultconfig_list[aVaultId]
