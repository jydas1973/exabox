#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/cluacceleratednetwork.py /main/3 2026/02/21 03:56:44 mpedapro Exp $
#
# cluacceleratednetwork.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      cluacceleratednetwork.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    mpedapro    02/03/26 - Enh::38914367 library functions for mtu setting and
#                           oeda bonding options
#    mpedapro    11/24/25 - Enh::38602758 add lib functions for sriov
#    mpedapro    11/12/25 - File to contain changes for sriov feature
#    mpedapro    11/12/25 - Creation
#

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogJson, ebLogCritical, ebLogTrace, gLogMgrDirectory
from exabox.core.Error import ebError, ExacloudRuntimeError, gNetworkError
from exabox.utils.node import (
    connect_to_host, node_cmd_abs_path_check,
    node_exec_cmd, node_exec_cmd_check, node_update_key_val_file,
    node_write_text_file, node_read_text_file
)
import ipaddress
import textwrap

#Constants
NETWORK_VIRTUALIZATION_XML_KEY = 'network_virtualization'
ACCELERATED_NETWORK_SUPPORT_EXABOX_PARAM = 'accelerated_network_support'
VIRTIO = 'virtio'
SRIOV = 'sriov'
NETWORK_VIRTUALIZATION_POSSIBLE_XML_KEYVALUEMAP = {
    VIRTIO : 'virtio',
    SRIOV  : 'sriov'
}
CLIENT_NETWORK_KEY = 'client'
BACKUP_NETWORK_KEY = 'backup'
CLIENT_ACCELERATED_NETWORK_SLAVES_DOMU_MASTER = 'eth1 eth2'
BACKUP_ACCELERATED_NETWORK_SLAVES_DOMU_MASTER = 'eth3 eth4'

class ebCluAcceleratedNetwork():

    @staticmethod
    def isFeatureSupported(ebCluControlObj):
        if ebCluControlObj.mIsExabm() and ebCluControlObj.mCheckConfigOption("accelerated_network_support", "True"):
            ebLogInfo('Accelerated Network Support is enabled')
            return True
        else:
            ebLogWarn('Accelerated Network Support is not enabled. Only ExaCS env is enabled with feature. Pls set exabox.conf param accelerated_network_support to True while running in ExaCS env')
            return False

    @staticmethod
    def isacceleratedNetworkCapableDom0(ebCluControlObj, dom0Name : str):
        dom0Model = ebCluControlObj.mGetExadataDom0Model()
        exadataInstalledVersion = int(ebCluControlObj.mGetImageVersion(dom0Name).split('.')[0])
        ebLogInfo("Dom0 :: " + dom0Name + " is of model :: " + dom0Model  + " with exadata installed version :: " + str(exadataInstalledVersion))
        if dom0Model != 'X11' or exadataInstalledVersion < 26:
            ebLogWarn("Dom0 :: " + dom0Name + " is not capable of supporting acceleratedNetwork feature")
            return False
        return True

    @staticmethod
    def validateEnvForacceletedNetworkFeature(ebCluControlObj, dom0Name):
        if not ebCluAcceleratedNetwork.isFeatureSupported(ebCluControlObj):
            detailedError = 'Accelerated Network Support is not enabled. Only ExaCS env is enabled with feature. Pls set exabox.conf param accelerated_network_support to True while running in ExaCS env'
            ebCluControlObj.mUpdateErrorObject(gNetworkError['ERROR_FEATURE_NOT_ENABLED'], detailedError)
            ebLogError(detailedError)
            raise ExacloudRuntimeError(0x0740, 0xA, detailedError)
        if not ebCluAcceleratedNetwork.isacceleratedNetworkCapableDom0(ebCluControlObj, dom0Name):
            detailedError = 'Dom0 :: ' + dom0Name + ' is not capable of supporting acceleratedNetwork feature. Only dom0 with X11 model and exadata version 26.x or higher supported'
            ebCluControlObj.mUpdateErrorObject(gNetworkError['ERROR_ACCELERATEDNETWORK_INCAPABLE_DOM0'], detailedError)
            ebLogError(detailedError)
            raise ExacloudRuntimeError(0x0740, 0xA, detailedError)

    @staticmethod
    def addAcceleratedNetworkOedaAction(ebCluControlObj, netId, ipv6Gateway, dom0Name, domuId, networkVirtualizationValue="virtio", listToAddOedaAction=[]):
        if ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(ebCluControlObj, dom0Name, domuId, networkVirtualizationValue):
            ebLogInfo('** Setting ACCELERATEDNETWORK property for network **' + netId + '**to value** ENABLED')
            propertiesToUpdate = {"ACCELERATEDNETWORK": 'ENABLED'}
            if ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetType() == "backup":
                propertiesToUpdate["slave"] = ebCluAcceleratedNetwork.getAcceleratedNetworkSlavesForDomuMaster("backup")
            _cmd = [
                "ALTER NETWORK",
                propertiesToUpdate,
                {"ID": netId}
            ]
            listToAddOedaAction.append(_cmd)
            ebCluAcceleratedNetwork.addBondingConfigOedaAction(ebCluControlObj, netId, ipv6Gateway, dom0Name, domuId, networkVirtualizationValue, listToAddOedaAction)
        return listToAddOedaAction

    @staticmethod
    def getBondingOptions(ebCluControlObj, gateWayIp, ipv6GatewayIp, slaves, domuId, mode='active-backup', fail_over_mac='0', num_grat_arp='8',arp_interval='1000', primary_reselect='failure', arp_allslaves='0'):
        preferredSlave = 'eth1'
        if slaves is not None:
            preferredSlave = slaves.split()[0]
        elif domuId is not None:
            hostName = ebCluControlObj.mGetMachines().mGetMachineConfig(domuId).mGetMacHostName()
            preferredSlave = ebCluControlObj.mGetNetworks().mGetNetworkConfigByName(hostName).mGetNetSlave().split('.')[0]
        bondOptions = 'mode={0} fail_over_mac={1} arp_interval={2} primary_reselect={3} arp_allslaves={4} primary={5}'.format(mode, fail_over_mac,
                                                                                               arp_interval, primary_reselect, arp_allslaves,preferredSlave)
        if ipaddress.ip_address(gateWayIp).version == 4:
            bondOptions = bondOptions + ' num_grat_arp={0} arp_ip_target={1}'.format(num_grat_arp, gateWayIp)
        elif ipaddress.ip_address(gateWayIp).version == 6:
            bondOptions = bondOptions + ' num_unsol_na={0} ns_ip6_target={1}'.format(num_grat_arp, gateWayIp)

        #For only dual stack ipv6GatewayIp will have to gateway ipv6 address. For single stack, it is None.
        if ipv6GatewayIp is not None and ipaddress.ip_address(ipv6GatewayIp).version == 6:
            bondOptions = bondOptions + ' num_unsol_na={0} ns_ip6_target={1}'.format(num_grat_arp, ipv6GatewayIp)

        return bondOptions

    @staticmethod
    def addBondingConfigOedaAction(ebCluControlObj, netId, ipv6Gateway, dom0Name, domuId, networkVirtualizationValue="virtio", listToAddOedaAction=[]):
        if ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(ebCluControlObj, dom0Name, domuId, networkVirtualizationValue):
            gatewayIp = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetGateWay()
            hostName = ebCluControlObj.mGetMachines().mGetMachineConfig(domuId).mGetMacHostName()
            networkType = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetType()
            slaves = ebCluAcceleratedNetwork.getAcceleratedNetworkSlavesForDomuMaster(networkType)
            ebLogInfo('** Setting Bonding configuration for for network **' + netId + '**to value**' + ebCluAcceleratedNetwork.getBondingOptions(ebCluControlObj, gatewayIp, ipv6Gateway, slaves, hostName))
            _cmd = [
                "ALTER NETWORK",
                {"BONDING_OPTS": ebCluAcceleratedNetwork.getBondingOptions(ebCluControlObj, gatewayIp, ipv6Gateway, slaves, hostName)},
                {"HOSTNAME": hostName, "networktype": networkType}
            ]
            listToAddOedaAction.append(_cmd)
        return listToAddOedaAction

    @staticmethod
    def checkInputAndValidateEnvForAcceleratedNetwork(ebCluControlObj, dom0Name, domuId, networkVirtualizationValue="virtio"):
        if networkVirtualizationValue is None or networkVirtualizationValue == 'UNDEFINED' or networkVirtualizationValue.lower() == NETWORK_VIRTUALIZATION_POSSIBLE_XML_KEYVALUEMAP[VIRTIO]:
            ebLogInfo("No need to enable accelerated network for domu :: " + domuId)
            return False
        elif networkVirtualizationValue is not None and networkVirtualizationValue.lower() == NETWORK_VIRTUALIZATION_POSSIBLE_XML_KEYVALUEMAP.get(SRIOV):
            ebCluAcceleratedNetwork.validateEnvForacceletedNetworkFeature(ebCluControlObj, dom0Name)
            ebLogInfo("Accelerated network option can be enabled for domu :: " + domuId)
            return True
        else:
            detailedError = 'Invalid network_virtualization value in payload. It should be one of ' + str(NETWORK_VIRTUALIZATION_POSSIBLE_XML_KEYVALUEMAP.keys())
            ebCluControlObj.mUpdateErrorObject(gNetworkError['INVALID_INPUT_PARAMETER'], detailedError)
            ebLogError(detailedError)
            raise ExacloudRuntimeError(0x0740, 0xA, detailedError)

    @staticmethod
    def isClusterEnabledWithAcceleratedNetwork(ebCluControlObj):
       try:
           #Returns true if both client and backup networks are sriov enabled.
           networkIds = ebCluControlObj.mGetNetworks().mGetNetworkIdList()
           networkConfigs = (ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId) for netId in networkIds)
           for netObj in networkConfigs:
               if netObj.mGetNetType() == CLIENT_NETWORK_KEY or netObj.mGetNetType() == BACKUP_NETWORK_KEY:
                   if netObj.mGetAcceleratedNetwork() is not None and netObj.mGetAcceleratedNetwork().lower() != 'ENABLED'.lower():
                       ebLogInfo(netObj.mGetNetId() + ' is not accelerated network enabled.')
                       return False
                   ebLogInfo(netObj.mGetNetId() + ' is accelerated network enabled.')
           return True
       except Exception as e:
           ebLogError('Could not verify accelerated network property. Exception :: '+ str(e))
           return False

    @staticmethod
    def isDom0InterfaceEnabledWithSwitchDevMode(node, vFinterfaceName):
        """
            Returns True if the given interface is virtual function and it's pf is in switch dev mode,
            otherwise returns False.
        """
        pciAddr = None
        try:
            binReadLinkAbsPath = node_cmd_abs_path_check(node, "readlink", sbin=False)
            readLinkCmd = f'{binReadLinkAbsPath} /sys/class/net/{vFinterfaceName}/device/physfn'
            retObj = node_exec_cmd(node, readLinkCmd, True, True, True, False, None)
            if retObj.exit_code != 0:
                ebLogWarn("Given interface :: " + vFinterfaceName + " in dom0 :: " + node.mGetHostname() + " is not virtual function.")
                return False
            #Get the physical function pci address from output.
            pciAddr = retObj.stdout.strip().split("/")[-1]
            if not pciAddr:
                ebLogWarn('Could not get PCI_SLOT_NAME from the out of ' + readLinkCmd + ' :: ' + retObj.stdout)
                return False
        except Exception as e:
            ebLogWarn('Exception occurred while getting PCI_SLOT_NAME. Exception :: '+ str(e))
            return False
        # Step 2: run devlink command to check whether pf pciAddr is in switch dev mode or not.
        try:
            binDevlinkAbsPath = node_cmd_abs_path_check(node, "devlink", sbin=True)
            devlinkCmd = f'{binDevlinkAbsPath} dev eswitch show pci/{pciAddr}'
            retObj = node_exec_cmd(node, devlinkCmd, True, True, True, False, None)
            if retObj.exit_code != 0:
                return False
            ebLogInfo('Ouput of ' + devlinkCmd + ' :: ' + retObj.stdout)
            for line in retObj.stdout.splitlines():
                if 'mode switchdev' in line:
                    return True
        except Exception as e:
            ebLogWarn('Exception occurred while getting nic mode. Exception :: '+ str(e))
            return False
        return False

    @staticmethod
    def getPhysicalFnCandidatesForVirtualFn(node, virtualFn):
        # Get all the PF candidates and returns true PF.
        binlsAbsPath = node_cmd_abs_path_check(node, "ls", sbin=True)
        pfCandidatesListCmd = f"{binlsAbsPath} /sys/class/net/{virtualFn}/device/physfn/net"
        retObj = node_exec_cmd(node, pfCandidatesListCmd, True, True, True, True, None)
        ebLogInfo('Ouput of ' + pfCandidatesListCmd + ' :: ' + retObj.stdout)
        return retObj.stdout.split()

    @staticmethod
    # Get the slaves of bondInterfaceName and returns vf slave that is associated with pf passed to this function
    def getVirtualFnSlaveForPhysicalFnSlave(node, bondInterfaceName, physicalInterfaceName):
        try:
            binCatAbsPath = node_cmd_abs_path_check(node, "cat", sbin=False)
            getSlavesCmd = f'{binCatAbsPath} /sys/class/net/{bondInterfaceName}/bonding/slaves'
            retObj = node_exec_cmd(node, getSlavesCmd, True, True, True, True, None)
            ebLogInfo('Ouput of ' + getSlavesCmd + ' :: ' + retObj.stdout)
            for slave in retObj.stdout.split():
                pfCandidates = ebCluAcceleratedNetwork.getPhysicalFnCandidatesForVirtualFn(node, slave)
                for pfCandidate in pfCandidates:
                    if pfCandidate == physicalInterfaceName:
                        return slave
            return None
        except Exception as e:
            ebLogWarn('Exception occurred while getting virtual fn associated with physical fn. Exception :: ' + str(e))
            return None

    @staticmethod
    def createIfcfgPfFile(node, interfaceName, filePath):
        '''
        As per suggestion from exadata team, we can create this file with below template.
        cat /etc/sysconfig/network-scripts/ifcfg-eth1pf
        #### DO NOT REMOVE THESE LINES ####
        #### %GENERATED BY CELL% ####
        DEVICE=eth1pf
        TYPE=Ethernet
        USERCTL=no
        ONBOOT=yes
        BOOTPROTO=none
        HOTPLUG=no
        IPV6INIT=no
        NM_CONTROLLED=no
        '''
        data = textwrap.dedent("""\
            DEVICE={interfaceName}
            TYPE=Ethernet
            USERCTL=no
            ONBOOT=yes
            BOOTPROTO=none
            MTU=9000
            HOTPLUG=no
            IPV6INIT=no
            NM_CONTROLLED=no
            """).format(interfaceName=interfaceName)
        ebLogInfo('Creating ' + filePath + ' with data :: ' + data)
        node_write_text_file(node, filePath, data)

    @staticmethod
    def setMtuForPhysicalFunction(node, virtualFunctionName):
        try:
            #Check if dom0 is enabled in switch dev mode for
            if ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode(node, virtualFunctionName):
                pfName = virtualFunctionName + "pf"
                ebLogInfo('Physical function for :: ' + virtualFunctionName + ' is :: ' + pfName)
                #Set MTU runtime with ip link set command.
                ipLinkAbsPath = node_cmd_abs_path_check(node, "ip", sbin=True)
                mtuSetCmd = f'{ipLinkAbsPath} link set dev {pfName} mtu 9000'
                node_exec_cmd(node, mtuSetCmd, True, True, True, False, None)
                #Set MTU in persistent setting.
                ifcfgFilePath = f'/etc/sysconfig/network-scripts/ifcfg-{pfName}'
                mtuMap = { "MTU": "9000" }
                if node.mFileExists(ifcfgFilePath):
                    node_update_key_val_file(node, ifcfgFilePath, mtuMap)
                else:
                    ebLogInfo('ifcfg file :: ' + ifcfgFilePath + ' is not present. Creating..')
                    ebCluAcceleratedNetwork.createIfcfgPfFile(node, pfName, ifcfgFilePath)
        except Exception as e:
            ebLogWarn('Exception occurred while setting MTU for physical function of virtual function ' + virtualFunctionName + '. Exception :: ' + str(e))
            return False
        return True

    @staticmethod
    def getAcceleratedNetworkSlavesForDomuMaster(networkType="client"):
        if networkType == CLIENT_NETWORK_KEY:
            return CLIENT_ACCELERATED_NETWORK_SLAVES_DOMU_MASTER
        elif networkType == BACKUP_NETWORK_KEY:
            return BACKUP_ACCELERATED_NETWORK_SLAVES_DOMU_MASTER
        return None
