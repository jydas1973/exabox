#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/cluacceleratednetwork.py /main/2 2025/12/01 04:43:08 mpedapro Exp $
#
# cluacceleratednetwork.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
    def addAcceleratedNetworkOedaAction(ebCluControlObj, netId, dom0Name, domuName, networkVirtualizationValue="virtio", listToAddOedaAction=[]):
        if ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(ebCluControlObj, dom0Name, domuName, networkVirtualizationValue):
            ebLogInfo('** Setting ACCELERATEDNETWORK property for network **' + netId + '**to value** ENABLED')
            propertiesToUpdate = {"ACCELERATEDNETWORK": 'ENABLED'}
            '''
            OEDA is yet to support below bonding_opts argument. Once it supports will uncomment and test this code.

            hostName = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetHostName()
            gatewayIp = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetGateWay()
            slaves = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetSlave()
            propertiesToUpdate["BONDING_OPTS"] = ebCluAcceleratedNetwork.getBondingOptions(ebCluControlObj, gatewayIp, slaves, hostName)
            '''
            _cmd = [
                "ALTER NETWORK",
                propertiesToUpdate,
                {"ID": netId}
            ]
            listToAddOedaAction.append(_cmd)
        return listToAddOedaAction

    @staticmethod
    def getBondingOptions(ebCluControlObj, gateWayIp, slaves, hostName, mode='active-backup', fail_over_mac='1', num_grat_arp='8',
                          arp_interval='1000', primary_reselect='failure', arp_allslaves='1'):
        preferredSlave = 'eth1'
        if slaves is not None:
            preferredSlave = slaves.split(' ')[0]
        elif hostName is not None:
            preferredSlave = ebCluControlObj.mGetNetworks().mGetNetworkConfigByName(hostName).mGetNetSlave().split('.')[0]

        return 'mode={0} fail_over_mac={1} num_grat_arp={2} arp_interval={3} primary_reselect={4} arp_allslaves={5} arp_ip_target={6} primary={7}'.format(mode, fail_over_mac, num_grat_arp,
                                                                                               arp_interval, primary_reselect, arp_allslaves,
                                                                                               gateWayIp, preferredSlave)

    @staticmethod
    def addBondingConfigOedaAction(ebCluControlObj, netId, dom0Name, domuName, networkVirtualizationValue="virtio", listToAddOedaAction=[]):
        if ebCluAcceleratedNetwork.checkInputAndValidateEnvForAcceleratedNetwork(ebCluControlObj, dom0Name, domuName, networkVirtualizationValue):
            ebLogInfo('** Setting Bonding configuration for for network **' + netId + '**to value**' + "")
            gatewayIp = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetGateWay()
            slaves = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetSlave()
            hostName = ebCluControlObj.mGetNetworks().mGetNetworkConfig(netId).mGetNetHostName()
            _cmd = [
                "ALTER NETWORK",
                {"BONDING_OPTS": ebCluAcceleratedNetwork.getBondingOptions(ebCluControlObj, gatewayIp, slaves, hostName)},
                {"ID": netId}
            ]
            listToAddOedaAction.append(_cmd)
        return listToAddOedaAction

    @staticmethod
    def checkInputAndValidateEnvForAcceleratedNetwork(ebCluControlObj, dom0Name, domuName, networkVirtualizationValue="virtio"):
        if networkVirtualizationValue is None or networkVirtualizationValue == 'UNDEFINED' or networkVirtualizationValue.lower() == NETWORK_VIRTUALIZATION_POSSIBLE_XML_KEYVALUEMAP[VIRTIO]:
            ebLogInfo("No need to enable accelerated network for domu :: " + domuName)
            return False
        elif networkVirtualizationValue is not None and networkVirtualizationValue.lower() == NETWORK_VIRTUALIZATION_POSSIBLE_XML_KEYVALUEMAP.get(SRIOV):
            ebCluAcceleratedNetwork.validateEnvForacceletedNetworkFeature(ebCluControlObj, dom0Name)
            ebLogInfo("Accelerated network option can be enabled for domu :: " + domuName)
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
    def isDom0InterfaceEnabledWithSwitchDevMode(node, interfaceName):
        """
            Returns True if the given interface is in switchdev mode using devlink,
            otherwise returns False.
        """
        # Step 1: find PCI address for the interface
        try:
            pciAddr = None
            binCatAbsPath = node_cmd_abs_path_check(node, "cat", sbin=False)
            ueventPathCmd = f'{binCatAbsPath} /sys/class/net/{interfaceName}/device/uevent'
            retObj = node_exec_cmd(node, ueventPathCmd, True, True, True, False, None)
            if retObj.exit_code != 0:
                return False
            ebLogInfo('Ouput of ' + ueventPathCmd + ' :: ' + retObj.stdout)
            outputLines = retObj.stdout.splitlines()
            for line in outputLines:
                if line.startswith("PCI_SLOT_NAME="):
                    pciAddr = line.strip().split("=", 1)[1]
                    break
        except Exception as e:
            ebLogWarn('Exception occurred while getting PCI_SLOT_NAME. Exception :: '+ str(e))
            return False

        if not pciAddr:
            ebLogWarn('Could not get PCI_SLOT_NAME from the out of ' + ueventPathCmd + ' :: ' + retObj.stdout)
            return False

        # Step 2: run devlink
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











